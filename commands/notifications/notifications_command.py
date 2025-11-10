from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType

from commands.notifications.notifications import get_notifications_keyboard

router = Router()


@router.message(Command("notifications"))
async def cmd_notifications(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    
    user_id = message.from_user.id
    keyboard = get_notifications_keyboard(user_id)
    
    await message.answer(
        "🔔 <b>Настройки уведомлений</b>\n\n"
        "Выберите, какие уведомления вы хотите получать:\n\n"
        "🟢 - уведомление <b>включено</b>\n"
        "🔴 - уведомление <b>выключено</b>",
        reply_markup=keyboard
    )
