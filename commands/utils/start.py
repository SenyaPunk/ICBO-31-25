from aiogram import Router
from aiogram.filters import Command, ChatMemberUpdatedFilter, KICKED
from aiogram.types import Message
from aiogram.enums import ChatType

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    
    user_name = message.from_user.first_name
    
    await message.answer(
        f"👋 <b>Привет, {user_name}!</b>\n\n"
        f"Я бот для вашей группы в институте.\n"
        f"Используй /help чтобы узнать список доступных команд.\n\n"
        f"💡 <i>Команды работают только в личных сообщениях!</i>"
    )
