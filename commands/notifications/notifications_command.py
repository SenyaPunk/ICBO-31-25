from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType

from commands.utils.notifications import get_notifications_keyboard

# Создаем роутер для команды /notifications
router = Router()


@router.message(Command("notifications"))
async def cmd_notifications(message: Message):
    """
    Обработчик команды /notifications
    Открывает настройки уведомлений
    """
    # Проверяем, что это личное сообщение
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
