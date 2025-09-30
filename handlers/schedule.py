from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from keyboards.inline import get_schedule_keyboard, get_back_button
from utils.schedule_parser import schedule_parser

router = Router()


@router.message(Command("schedule"))
async def cmd_schedule(message: Message):
    """Обработчик команды /schedule"""
    await message.answer(
        "📅 <b>Расписание занятий</b>\n\nВыбери день недели:",
        reply_markup=get_schedule_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "schedule")
async def show_schedule_menu(callback: CallbackQuery):
    """Показать меню выбора дня"""
    await callback.message.edit_text(
        "📅 <b>Расписание занятий</b>\n\nВыбери день недели:",
        reply_markup=get_schedule_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("schedule_"))
async def show_day_schedule(callback: CallbackQuery):
    """Показать расписание на конкретный день"""
    day = callback.data.split("_")[1]
    
    day_names = {
        'monday': 'понедельник',
        'tuesday': 'вторник',
        'wednesday': 'среда',
        'thursday': 'четверг',
        'friday': 'пятница',
        'saturday': 'суббота'
    }
    
    day_names_ru = {
        'monday': 'Понедельник',
        'tuesday': 'Вторник',
        'wednesday': 'Среда',
        'thursday': 'Четверг',
        'friday': 'Пятница',
        'saturday': 'Суббота'
    }
    
    day_ru = day_names.get(day, 'понедельник')
    lessons = schedule_parser.get_day_schedule(day_ru)
    
    if not lessons:
        schedule_text = "Нет занятий 🎉"
    else:
        schedule_lines = []
        for i, lesson in enumerate(lessons, 1):
            lesson_type = lesson.get('type', '')
            type_emoji = {
                'Лекция': '📚',
                'Практика': '✏️',
                'Лабораторная': '🔬'
            }.get(lesson_type, '📖')
            
            schedule_lines.append(
                f"{i}. {lesson['time']} {type_emoji}\n"
                f"   <b>{lesson['subject']}</b>\n"
                f"   👨‍🏫 {lesson['teacher']}\n"
                f"   🚪 {lesson['room']}"
            )
        schedule_text = "\n\n".join(schedule_lines)
    
    text = (
        f"📅 <b>Расписание на {day_names_ru[day]}</b>\n\n"
        f"{schedule_text}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()
