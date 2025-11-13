from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType
import logging

from commands.schedule.schedule_parser import (
    fetch_ics_from_json, 
    parse_schedule, 
    get_week_lessons,
    get_today_lessons,
    format_schedule_message,
    URL,
    get_week_number
)

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("schedule"))
async def cmd_schedule(message: Message):
    
    try:
        loading_msg = await message.answer("⏳ Загружаю расписание на неделю...")
        
        ical_str = fetch_ics_from_json(URL)
        events = parse_schedule(ical_str)
        week_events = get_week_lessons(events)
        
        schedule_text = format_schedule_message(week_events, "неделю")
        
        import datetime
        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=today.weekday())
        week_end = week_start + datetime.timedelta(days=6)
        
        week_num = get_week_number(week_start)
        
        header = (
            f"📚 <b>Расписание на неделю</b> (неделя {week_num})\n"
            f"📆 {week_start.strftime('%d.%m')} — {week_end.strftime('%d.%m.%Y')}\n"
            f"{schedule_text}"
        )
        
        await loading_msg.edit_text(header)
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке расписания: {e}")
        await message.answer(
            f"❌ Ошибка при загрузке расписания\n\n"
            f"Пожалуйста, попробуйте позже или обратитесь к администратору."
        )

@router.message(Command("today"))
async def cmd_today_schedule(message: Message):
    
    
    try:
        loading_msg = await message.answer("⏳ Загружаю расписание на сегодня...")
        
        ical_str = fetch_ics_from_json(URL)
        events = parse_schedule(ical_str)
        today_events = get_today_lessons(events)
        
        import datetime
        today = datetime.date.today()
        schedule_text = format_schedule_message(today_events, "день")
        
        header = (
            f"📚 <b>Расписание на сегодня</b>\n"
            f"📆 {today.strftime('%d.%m.%Y')}\n"
            f"{schedule_text}"
        )
        
        await loading_msg.edit_text(header)
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке расписания: {e}")
        await message.answer(
            f"❌ Ошибка при загрузке расписания\n\n"
            f"Пожалуйста, попробуйте позже или обратитесь к администратору."
        )
