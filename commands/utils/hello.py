from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType
from datetime import datetime
from dateutil import tz

router = Router()

@router.message(Command("hello"))
async def cmd_hello(message: Message):

    if message.chat.type != ChatType.PRIVATE:
        return
    
    user_name = message.from_user.first_name
    moscow_tz = tz.gettz("Europe/Moscow")
    current_hour = datetime.now(moscow_tz).hour
    
    if 5 <= current_hour < 12:
        greeting = "Доброе утро"
        emoji = "🌅"
    elif 12 <= current_hour < 17:
        greeting = "Добрый день"
        emoji = "☀️"
    elif 17 <= current_hour < 22:
        greeting = "Добрый вечер"
        emoji = "🌆"
    else:
        greeting = "Доброй ночи"
        emoji = "🌙"
    
    await message.answer(
        f"{emoji} <b>{greeting}, {user_name}!</b>\n\n"
        f"Рад тебя видеть! 😊\n"
        f"Чем могу помочь?"
    )
