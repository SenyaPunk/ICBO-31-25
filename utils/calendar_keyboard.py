"""
Модуль для создания интерактивного календаря в Telegram боте.
Позволяет выбирать дату с помощью inline-кнопок.
"""

import calendar
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
from dateutil import tz

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class CalendarKeyboard:
    
    MONTHS_RU = [
        "", "янв", "фев", "мар", "апр", "май", "июн",
        "июл", "авг", "сен", "окт", "ноя", "дек"
    ]
    
    WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    
    def __init__(self, callback_prefix: str = "cal"):
        
        self.callback_prefix = callback_prefix
        self.moscow_tz = tz.gettz("Europe/Moscow")
    
    def _get_today(self) -> date:
        return datetime.now(self.moscow_tz).date()
    
    def create_calendar(
        self, 
        year: Optional[int] = None, 
        month: Optional[int] = None,
        min_date: Optional[date] = None,
        max_date: Optional[date] = None
    ) -> InlineKeyboardMarkup:
        
        today = self._get_today()
        
        if year is None:
            year = today.year
        if month is None:
            month = today.month
        
        if min_date is None:
            min_date = today
        
        buttons = []
        
        year_nav = []
        year_nav.append(InlineKeyboardButton(
            text="<<",
            callback_data=f"{self.callback_prefix}:prev_year:{year}:{month}"
        ))
        year_nav.append(InlineKeyboardButton(
            text=f"[{year}]",
            callback_data=f"{self.callback_prefix}:ignore"
        ))
        year_nav.append(InlineKeyboardButton(
            text=">>",
            callback_data=f"{self.callback_prefix}:next_year:{year}:{month}"
        ))
        buttons.append(year_nav)
        
        month_nav = []
        month_nav.append(InlineKeyboardButton(
            text="<",
            callback_data=f"{self.callback_prefix}:prev_month:{year}:{month}"
        ))
        month_nav.append(InlineKeyboardButton(
            text=f"[{self.MONTHS_RU[month]}]",
            callback_data=f"{self.callback_prefix}:ignore"
        ))
        month_nav.append(InlineKeyboardButton(
            text=">",
            callback_data=f"{self.callback_prefix}:next_month:{year}:{month}"
        ))
        buttons.append(month_nav)
        
        weekday_buttons = []
        for i, day_name in enumerate(self.WEEKDAYS_RU):
            text = f"[{day_name}]" if i == 6 else day_name
            weekday_buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=f"{self.callback_prefix}:ignore"
            ))
        buttons.append(weekday_buttons)
        
        cal = calendar.Calendar(firstweekday=0)  
        month_days = cal.monthdayscalendar(year, month)
        
        for week in month_days:
            week_buttons = []
            for day_num in week:
                if day_num == 0:
                    week_buttons.append(InlineKeyboardButton(
                        text=" ",
                        callback_data=f"{self.callback_prefix}:ignore"
                    ))
                else:
                    current_date = date(year, month, day_num)
                    
                    is_available = True
                    if min_date and current_date < min_date:
                        is_available = False
                    if max_date and current_date > max_date:
                        is_available = False
                    
                    if current_date == today:
                        text = f"[{day_num}]"  
                    elif current_date.weekday() == 6:
                        text = f"[{day_num}]"  
                    else:
                        text = str(day_num)
                    
                    if is_available:
                        callback = f"{self.callback_prefix}:select:{year}:{month}:{day_num}"
                    else:
                        callback = f"{self.callback_prefix}:ignore"
                        text = f"·{day_num}·" if current_date < min_date else text
                    
                    week_buttons.append(InlineKeyboardButton(
                        text=text,
                        callback_data=callback
                    ))
            
            buttons.append(week_buttons)
        
        bottom_buttons = []
        bottom_buttons.append(InlineKeyboardButton(
            text="Отмена",
            callback_data=f"{self.callback_prefix}:cancel"
        ))
        bottom_buttons.append(InlineKeyboardButton(
            text="Сегодня",
            callback_data=f"{self.callback_prefix}:today"
        ))
        buttons.append(bottom_buttons)
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def parse_callback(self, callback_data: str) -> Tuple[str, Optional[date], int, int]:
        
        parts = callback_data.split(":")
        
        if len(parts) < 2:
            return ("ignore", None, 0, 0)
        
        action = parts[1]
        
        if action == "select" and len(parts) == 5:
            year = int(parts[2])
            month = int(parts[3])
            day = int(parts[4])
            return (action, date(year, month, day), year, month)
        
        elif action in ["prev_month", "next_month", "prev_year", "next_year"] and len(parts) == 4:
            year = int(parts[2])
            month = int(parts[3])
            
            if action == "prev_month":
                if month == 1:
                    month = 12
                    year -= 1
                else:
                    month -= 1
            elif action == "next_month":
                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1
            elif action == "prev_year":
                year -= 1
            elif action == "next_year":
                year += 1
            
            return (action, None, year, month)
        
        elif action == "today":
            today = self._get_today()
            return (action, today, today.year, today.month)
        
        elif action == "cancel":
            return (action, None, 0, 0)
        
        return ("ignore", None, 0, 0)


homework_calendar = CalendarKeyboard(callback_prefix="hw_cal")
control_calendar = CalendarKeyboard(callback_prefix="km_cal")
quick_homework_calendar = CalendarKeyboard(callback_prefix="qhw_cal")

def format_date_ru(d: date) -> str:
    WEEKDAYS_SHORT = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
    weekday = WEEKDAYS_SHORT[d.weekday()]
    return f"{weekday} ({d.strftime('%d.%m.%Y')})"
