from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from keyboards.inline import get_back_button

router = Router()

# Пример домашних заданий (замените на реальные)
HOMEWORK_DATA = [
    {
        'subject': 'Математический анализ',
        'task': 'Решить задачи №15-20 из учебника',
        'deadline': '15.10.2024'
    },
    {
        'subject': 'Программирование',
        'task': 'Реализовать алгоритм сортировки слиянием',
        'deadline': '12.10.2024'
    },
    {
        'subject': 'Базы данных',
        'task': 'Создать ER-диаграмму для проекта',
        'deadline': '18.10.2024'
    },
    {
        'subject': 'Веб-разработка',
        'task': 'Сверстать адаптивную страницу портфолио',
        'deadline': '20.10.2024'
    }
]


@router.message(Command("homework"))
async def cmd_homework(message: Message):
    """Обработчик команды /homework"""
    await show_homework_list(message)


@router.callback_query(F.data == "homework")
async def show_homework_callback(callback: CallbackQuery):
    """Показать список домашних заданий через callback"""
    await show_homework_list(callback.message, is_callback=True)
    await callback.answer()


async def show_homework_list(message: Message, is_callback: bool = False):
    """Показать список домашних заданий"""
    if not HOMEWORK_DATA:
        text = "📚 <b>Домашние задания</b>\n\n✅ Все задания выполнены!"
    else:
        text = "📚 <b>Домашние задания</b>\n\n"
        for i, hw in enumerate(HOMEWORK_DATA, 1):
            text += (
                f"{i}. <b>{hw['subject']}</b>\n"
                f"   📝 {hw['task']}\n"
                f"   📅 Срок: {hw['deadline']}\n\n"
            )
    
    if is_callback:
        await message.edit_text(
            text,
            reply_markup=get_back_button(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            text,
            reply_markup=get_back_button(),
            parse_mode="HTML"
        )
