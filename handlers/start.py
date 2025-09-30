from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, WebAppInfo
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import GROUP_INFO, WEB_APP_URL

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    welcome_text = (
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
        f"Я бот для группы <b>{GROUP_INFO['name']}</b>\n"
        f"{GROUP_INFO['faculty']}, {GROUP_INFO['course']}\n\n"
        f"🚀 Открой приложение для удобного доступа ко всем функциям:\n"
        f"• Расписание занятий\n"
        f"• Домашние задания\n"
        f"• Информация о группе\n"
        f"• Уведомления\n\n"
        f"Нажми на кнопку ниже, чтобы открыть приложение 👇"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Открыть приложение",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ],
        [
            InlineKeyboardButton(text="ℹ️ Справка", callback_data="help")
        ]
    ])
    
    await message.answer(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    welcome_text = (
        f"🏠 <b>Главное меню</b>\n\n"
        f"Открой приложение для доступа ко всем функциям!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Открыть приложение",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ],
        [
            InlineKeyboardButton(text="ℹ️ Справка", callback_data="help")
        ]
    ])
    
    await callback.message.edit_text(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Показать справку"""
    help_text = (
        "ℹ️ <b>Справка по боту</b>\n\n"
        "<b>Как пользоваться:</b>\n"
        "1. Нажми кнопку 'Открыть приложение'\n"
        "2. Приложение откроется прямо в Telegram\n"
        "3. Используй меню для навигации\n\n"
        "<b>Доступные разделы:</b>\n"
        "📅 Расписание - актуальное расписание занятий\n"
        "📚 Домашние задания - список заданий с дедлайнами\n"
        "👥 Информация о группе - контакты и ссылки\n"
        "🔔 Уведомления - важные объявления\n\n"
        "💡 Все данные всегда под рукой в удобном интерфейсе!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")
        ]
    ])
    
    await callback.message.edit_text(
        help_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()
