

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from dateutil import tz

from commands.homework.homework_storage import homework_storage
from commands.homework.homework_command import format_date_ru, WEEKDAYS_RU

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("km"))
async def cmd_control_measures(message: Message):
    homework_storage.reload_data()
    
    upcoming_km = homework_storage.get_all_upcoming_control_measures()
    
    text = "📋 <b>Контрольные мероприятия</b>\n\n"
    
    if not upcoming_km:
        text += "🎉 На данный момент нет запланированных КМ!"
    else:
        for km_date, subject, descriptions in upcoming_km:
            date_str = format_date_ru(km_date)
            text += f"📅 <b>{date_str}</b>\n"
            text += f"   📖 {subject}\n"
            for desc in descriptions:
                text += f"      ⚠️ {desc}\n"
            text += "\n"
    
    await message.answer(text, parse_mode="HTML")


@router.message(Command("km_week"))
async def cmd_km_week(message: Message):
    moscow_tz = tz.gettz("Europe/Moscow")
    today = datetime.now(moscow_tz).date()
    
    homework_storage.reload_data()
    
    text = "📋 <b>Контрольные мероприятия на текущую неделю</b>\n\n"
    
    has_any = False
    
    for i in range(7):
        check_date = today + timedelta(days=i)
        km = homework_storage.get_control_measures_for_date(check_date)
        
        if km:
            has_any = True
            date_str = format_date_ru(check_date)
            text += f"📆 <b>{date_str}</b>\n"
            
            for subject, descriptions in km.items():
                text += f"   ⚠️ {subject}\n"
                for desc in descriptions:
                    text += f"      🔸 {desc}\n"
            
            text += "\n"
    
    if not has_any:
        text += "🎉 На эту неделю КМ не запланировано!"
    
    await message.answer(text, parse_mode="HTML")


@router.message(Command("hw_today"))
async def cmd_hw_today(message: Message):
    moscow_tz = tz.gettz("Europe/Moscow")
    today = datetime.now(moscow_tz).date()
    
    homework_storage.reload_data()
    hw = homework_storage.get_homework_for_date(today)
    km = homework_storage.get_control_measures_for_date(today)
    
    date_str = format_date_ru(today)
    text = f"📅 <b>Задания на сегодня ({date_str})</b>\n\n"
    
    if not hw and not km:
        text += "🎉 На сегодня заданий нет!"
    else:
        if hw:
            text += "📝 <b>Домашние задания:</b>\n"
            for subject, tasks in hw.items():
                text += f"\n📖 {subject}\n"
                for task in tasks:
                    text += f"   • {task}\n"
        
        if km:
            text += "\n📋 <b>Контрольные мероприятия:</b>\n"
            for subject, descriptions in km.items():
                text += f"\n📖 {subject}\n"
                for desc in descriptions:
                    text += f"   ⚠️ {desc}\n"
    
    await message.answer(text, parse_mode="HTML")


@router.message(Command("hw_tomorrow"))
async def cmd_hw_tomorrow(message: Message):
    moscow_tz = tz.gettz("Europe/Moscow")
    tomorrow = datetime.now(moscow_tz).date() + timedelta(days=1)
    
    homework_storage.reload_data()
    hw = homework_storage.get_homework_for_date(tomorrow)
    km = homework_storage.get_control_measures_for_date(tomorrow)
    
    date_str = format_date_ru(tomorrow)
    text = f"📅 <b>Задания на завтра ({date_str})</b>\n\n"
    
    if not hw and not km:
        text += "🎉 На завтра заданий нет!"
    else:
        if hw:
            text += "📝 <b>Домашние задания:</b>\n"
            for subject, tasks in hw.items():
                text += f"\n📖 {subject}\n"
                for task in tasks:
                    text += f"   • {task}\n"
        
        if km:
            text += "\n📋 <b>Контрольные мероприятия:</b>\n"
            for subject, descriptions in km.items():
                text += f"\n📖 {subject}\n"
                for desc in descriptions:
                    text += f"   ⚠️ {desc}\n"
    
    await message.answer(text, parse_mode="HTML")


@router.message(Command("hw_week"))
async def cmd_hw_week(message: Message):
    moscow_tz = tz.gettz("Europe/Moscow")
    today = datetime.now(moscow_tz).date()
    
    homework_storage.reload_data()
    
    text = "📅 <b>Задания на текущую неделю</b>\n\n"
    
    has_any = False
    
    for i in range(7):
        check_date = today + timedelta(days=i)
        hw = homework_storage.get_homework_for_date(check_date)
        km = homework_storage.get_control_measures_for_date(check_date)
        
        if hw or km:
            has_any = True
            date_str = format_date_ru(check_date)
            text += f"📆 <b>{date_str}</b>\n"
            
            if hw:
                for subject, tasks in hw.items():
                    text += f"   📝 {subject}\n"
                    for task in tasks:
                        text += f"      • {task}\n"
            
            if km:
                for subject, descriptions in km.items():
                    text += f"   ⚠️ {subject}\n"
                    for desc in descriptions:
                        text += f"      🔸 {desc}\n"
            
            text += "\n"
    
    if not has_any:
        text += "🎉 На эту неделю заданий нет!"
    
    await message.answer(text, parse_mode="HTML")
