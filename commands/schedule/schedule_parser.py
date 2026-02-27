import requests
import datetime
import re
from icalendar import Calendar
from dateutil import rrule, tz 
from dateutil.rrule import rrulestr, rruleset

URL = "https://schedule-of.mirea.ru/?s=1_5578"


def fetch_ics_from_json(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    text = requests.get(url, headers=headers).text

    m = re.search(r'"iCalContent"\s*:\s*"([^"]+)"', text)
    if not m:
        raise ValueError("Не найден iCalContent")

    ical_raw = m.group(1)
    ical_decoded = bytes(ical_raw, "utf-8").decode("unicode_escape")

    try:
        ical_decoded = ical_decoded.encode("latin1").decode("utf-8")
    except UnicodeEncodeError:
        pass

    return ical_decoded


def parse_schedule(ical_str):
    cal = Calendar.from_ical(ical_str)
    tz_moscow = tz.gettz("Europe/Moscow")
    events = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        start = component.get("DTSTART").dt
        end = component.get("DTEND").dt

        if isinstance(start, datetime.date) and not isinstance(start, datetime.datetime):
            start = datetime.datetime.combine(start, datetime.time(0, 0))
        if isinstance(end, datetime.date) and not isinstance(end, datetime.datetime):
            end = datetime.datetime.combine(end, datetime.time(23, 59))

        start = start.astimezone(tz_moscow) if start.tzinfo else start.replace(tzinfo=tz_moscow)
        end = end.astimezone(tz_moscow) if end.tzinfo else end.replace(tzinfo=tz_moscow)

        title = str(component.get("SUMMARY", "Без названия")).strip()
        location = str(component.get("LOCATION", "")).strip()
        teacher = str(component.get("DESCRIPTION", "")).strip()

        event_obj = {
            "start": start,
            "end": end,
            "title": title,
            "location": location,
            "teacher": teacher
        }

        if not is_all_day_event(event_obj):
            events.append(event_obj)



        if component.get("RRULE") or component.get("RDATE") or component.get("EXDATE"):
            rrset = rruleset()

            rr_raw = ""
            try:
                rr_raw = component.get("RRULE").to_ical().decode() if component.get("RRULE") else ""
            except Exception:
                pass
            if rr_raw:
                rr_text = rr_raw if rr_raw.upper().startswith("RRULE:") else "RRULE:" + rr_raw
                rrset.rrule(rrulestr(rr_text, dtstart=start))

            rdate_prop = component.get("RDATE")
            if rdate_prop:
                try:
                    for rd in rdate_prop.dts:
                        rd_dt = rd.dt
                        if isinstance(rd_dt, datetime.date) and not isinstance(rd_dt, datetime.datetime):
                            rd_dt = datetime.datetime.combine(rd_dt, start.time())
                        rd_dt = rd_dt.astimezone(tz_moscow) if getattr(rd_dt, "tzinfo", None) else rd_dt.replace(tzinfo=tz_moscow)
                        rrset.rdate(rd_dt)
                except Exception:
                    rd_dt = getattr(rdate_prop, "dt", None)
                    if rd_dt:
                        if isinstance(rd_dt, datetime.date) and not isinstance(rd_dt, datetime.datetime):
                            rd_dt = datetime.datetime.combine(rd_dt, start.time())
                        rd_dt = rd_dt.astimezone(tz_moscow) if getattr(rd_dt, "tzinfo", None) else rd_dt.replace(tzinfo=tz_moscow)
                        rrset.rdate(rd_dt)

            exdate_prop = component.get("EXDATE")
            if exdate_prop:
                try:
                    for ed in exdate_prop.dts:
                        ed_dt = ed.dt
                        if isinstance(ed_dt, datetime.date) and not isinstance(ed_dt, datetime.datetime):
                            ed_dt = datetime.datetime.combine(ed_dt, start.time())
                        ed_dt = ed_dt.astimezone(tz_moscow) if getattr(ed_dt, "tzinfo", None) else ed_dt.replace(tzinfo=tz_moscow)
                        rrset.exdate(ed_dt)
                except Exception:
                    ed_dt = getattr(exdate_prop, "dt", None)
                    if ed_dt:
                        if isinstance(ed_dt, datetime.date) and not isinstance(ed_dt, datetime.datetime):
                            ed_dt = datetime.datetime.combine(ed_dt, start.time())
                        ed_dt = ed_dt.astimezone(tz_moscow) if getattr(ed_dt, "tzinfo", None) else ed_dt.replace(tzinfo=tz_moscow)
                        rrset.exdate(ed_dt)

            until = start + datetime.timedelta(days=365)
            try:
                decoded_rr = component.decoded("RRULE")
                until_raw = decoded_rr.get(b"UNTIL", [None])[0] if isinstance(decoded_rr, dict) else None
                if until_raw:
                    until = until_raw if isinstance(until_raw, datetime.datetime) else datetime.datetime.combine(until_raw, datetime.time(23, 59), tz_moscow)
            except Exception:
                pass

            try:
                occurrences = rrset.between(start, until, inc=True)
            except Exception:
                occurrences = [start]

            for occ in occurrences:
                if occ == start:
                    continue
                occ = occ.astimezone(tz_moscow) if getattr(occ, "tzinfo", None) else occ.replace(tzinfo=tz_moscow)
                occ_event = {
                    "start": occ,
                    "end": occ + (end - start),
                    "title": title,
                    "location": location,
                    "teacher": teacher
                }

                if not is_service_event(title) and not is_all_day_event(occ_event):
                    events.append(occ_event)

    return events

def is_all_day_event(event):
    try:
        duration = event["end"] - event["start"]
        return duration >= datetime.timedelta(hours=23, minutes=58)
    except Exception:
        return False


def is_service_event(title):
    service_keywords = ['неделя', 'расписание', 'каникулы', 'выходной', 'праздник']
    title_lower = title.lower().strip()
    return any(k in title_lower for k in service_keywords) or re.match(r'^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}$', title_lower)


def get_week_lessons(events, week_start=None):
    if week_start is None:
        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=today.weekday())

    week_end = week_start + datetime.timedelta(days=6)
    week_events = [
        e for e in events if week_start <= e["start"].date() <= week_end and not is_service_event(e["title"])
    ]
    return sorted(week_events, key=lambda x: x["start"])


def get_today_lessons(events):
    today = datetime.date.today()
    return sorted(
        [e for e in events if e["start"].date() == today and not is_service_event(e["title"])],
        key=lambda x: x["start"]
    )


def extract_teacher_name(teacher_str):
    if not teacher_str:
        return ""
    t = re.split(r'группы:', teacher_str, flags=re.IGNORECASE)[0]
    t = re.sub(r'(?i)преподаватель\s*:?\s*', '', t)
    t = re.sub(r'\b[А-ЯA-ZЁ]{1,5}-\d{1,3}-\d{1,3}\b', '', t)
    t = re.sub(r'\s*\([^)]*\)\s*', ' ', t)
    parts = [p.strip() for p in t.split(',') if p.strip()]
    return ' '.join(parts[0].split()) if parts else t.strip()


def get_week_number(date):
    semester_start = datetime.date(date.year if date.month >= 9 else date.year - 1, 9, 1)
    if date < semester_start:
        semester_start = datetime.date(date.year - 1, 9, 1)
    return (date - semester_start).days // 7 + 1

def get_week_number_from_events(events, date=None):
    if date is None:
        date = datetime.date.today()

    monday = date - datetime.timedelta(days=date.weekday())

    for e in events:
        event_date = e["start"].date()
        if event_date == monday:
            title = e["title"].strip().lower()
            print("WEEK MARKER EVENT RAW TITLE:", repr(title))
            match = re.search(r'(\d+)\s*[-]?\s*недел', title)
            if match:
                return int(match.group(1))

    return get_week_number(date)


def format_schedule_message(events, period_name="неделю"):
    if not events:
        return f"В этой {period_name} пар нет! 🎉"

    day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    days_dict = {}

    for e in events:
        day_date = e["start"].date()
        key = f"{day_names[day_date.weekday()]} ({day_date.strftime('%d.%m')})"
        days_dict.setdefault(key, []).append(e)

    message = ""
    for day_key, day_events in days_dict.items():
        unique = {}
        for e in day_events:
            key = (f"{e['start'].strftime('%H:%M')}-{e['end'].strftime('%H:%M')}", e['title'])
            if key not in unique:
                unique[key] = e
            else:
                existing = unique[key]
                locations = set(existing['location'].split()) | set(e['location'].split())
                existing['location'] = ' '.join(sorted(locations))
                if not existing['teacher'] and e['teacher']:
                    existing['teacher'] = e['teacher']
        day_events = sorted(unique.values(), key=lambda x: x["start"])

        message += f"\n{'━' * 12}\n📅 <b>{day_key}</b>\n"
        for i, e in enumerate(day_events, 1):
            time_str = f"{e['start'].strftime('%H:%M')} - {e['end'].strftime('%H:%M')}"
            match = re.match(r'^(ЛК|ПР|ЛАБ)\s+(.+)', e['title'])
            lesson_type, title = (match.group(1), match.group(2)) if match else ("", e['title'])
            message += f"\n<b>{i}️⃣  {lesson_type} {title}</b>\n🕐 {time_str}"
            if e['location']:
                message += f"  •  📍 {e['location']}\n"
            else:
                message += "\n"
            teacher = extract_teacher_name(e['teacher'])
            if teacher:
                message += f"👤 Преподаватель: <b>{teacher}</b>\n"

    return message
