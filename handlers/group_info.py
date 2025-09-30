from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from keyboards.inline import get_back_button
from config import GROUP_INFO

router = Router()


@router.message(Command("group"))
async def cmd_group_info(message: Message):
    """Обработчик команды /group"""
    await show_group_info(message)


@router.callback_query(F.data == "group_info")
async def show_group_info_callback(callback: CallbackQuery):
    """Показать информацию о группе через callback"""
    await show_group_info(callback.message, is_callback=True)
    await callback.answer()


async def show_group_info(message: Message, is_callback: bool = False):
    """Показать информацию о группе"""
    text = (
        f"👥 <b>Информация о группе</b>\n\n"
        f"📌 Название: <b>{GROUP_INFO['name']}</b>\n"
        f"🎓 Курс: {GROUP_INFO['course']}\n"
        f"🏛 Факультет: {GROUP_INFO['faculty']}\n"
        f"👨‍🎓 Количество студентов: {GROUP_INFO['students_count']}\n\n"
        f"📱 <b>Полезные ссылки:</b>\n"
        f"• Чат группы: [добавьте ссылку]\n"
        f"• Электронный деканат: [добавьте ссылку]\n"
        f"• Расписание онлайн: [добавьте ссылку]"
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
