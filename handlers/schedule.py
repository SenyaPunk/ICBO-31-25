from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from keyboards.inline import get_schedule_keyboard, get_back_button

router = Router()

# Пример расписания (замените на реальное)
SCHEDULE_DATA = {
    'monday': [
        "1. 09:00-10:30 - Математический анализ (лекция) - ауд. 301",
        "2. 10:45-12:15 - Программирование (практика) - ауд. 205",
        "3. 12:30-14:00 - Английский язык - ауд. 410"
    ],
    'tuesday': [
        "1. 09:00-10:30 - Базы данных (лекция) - ауд. 302",
        "2. 10:45-12:15 - Базы данных (лаб.) - ауд. 206",
        "3. 12:30-14:00 - Физическая культура - Спортзал"
    ],
    'wednesday': [
        "1. 09:00-10:30 - Алгоритмы (лекция) - ауд. 301",
        "2. 10:45-12:15 - Алгоритмы (практика) - ауд. 205",
        "3. 12:30-14:00 - Веб-разработка (лаб.) - ауд. 207"
    ],
    'thursday': [
        "1. 09:00-10:30 - Операционные системы (лекция) - ауд. 303",
        "2. 10:45-12:15 - Операционные системы (лаб.) - ауд. 208",
    ],
    'friday': [
        "1. 09:00-10:30 - Математический анализ (практика) - ауд. 301",
        "2. 10:45-12:15 - Программирование (лаб.) - ауд. 205",
        "3. 12:30-14:00 - Философия (лекция) - ауд. 501"
    ],
    'saturday': [
        "Выходной! 🎉"
    ]
}


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
        'monday': 'Понедельник',
        'tuesday': 'Вторник',
        'wednesday': 'Среда',
        'thursday': 'Четверг',
        'friday': 'Пятница',
        'saturday': 'Суббота'
    }
    
    schedule = SCHEDULE_DATA.get(day, ["Нет занятий"])
    schedule_text = "\n".join(schedule)
    
    text = (
        f"📅 <b>Расписание на {day_names[day]}</b>\n\n"
        f"{schedule_text}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()
