from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType

router = Router()

@router.message(Command("help"))
async def cmd_help(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    
    help_text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/hello - Получить приветствие\n\n"
        "ℹ️ <i>Все команды работают только в личных сообщениях с ботом.</i>\n"
        "📚 <i>В будущем будет добавлено больше функций!</i>"
    )
    
    await message.answer(help_text)
