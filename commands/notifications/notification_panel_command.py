from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatType
from typing import Optional

from commands.group.group_manager import group_manager, Role

router = Router()


class NotificationStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_message = State()


NOTIFICATION_CATEGORIES = {
    "bot_updates": "🤖 Обновление бота",
    "control_works": "📝 Новые контрольные мероприятия",
    "homework": "📚 Новые домашки",
    "proforg": "🎭 Профорг",
    "schedule_changes": "📅 Изменения в расписании"
}


def is_allowed_to_send_notifications(user_id: int) -> tuple[bool, Optional[str]]:
    member = group_manager.get_member(user_id)
    if not member:
        return False, None
    
    role = member.get('role')
    if role in [Role.STAROSTA.value, Role.ZAM_STAROSTA.value, Role.PROFORG.value]:
        return True, role
    
    return False, None


@router.message(Command("notif_panel"))
async def cmd_notif_panel(message: Message, state: FSMContext):
    if message.chat.type != ChatType.PRIVATE:
        return
    
    user_id = message.from_user.id
    
    allowed, user_role = is_allowed_to_send_notifications(user_id)
    
    if not allowed:
        await message.answer(
            "❌ <b>Доступ запрещен</b>\n\n"
            "Данная команда доступна только старосте, заму старосты и профоргу."
        )
        return
    
    if user_role == Role.PROFORG.value:
        await state.update_data(notification_category="proforg")
        await state.set_state(NotificationStates.waiting_for_message)
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="❌ Отмена", callback_data="notif_cancel")
            ]]
        )
        
        await message.answer(
            f"📝 <b>Отправка уведомления</b>\n\n"
            f"Категория: <b>{NOTIFICATION_CATEGORIES['proforg']}</b>\n\n"
            f"Теперь отправьте сообщение, которое нужно разослать участникам.\n\n"
            f"Вы можете отправить любой тип сообщения, и оно будет переслано "
            f"с сохранением всего оригинального оформления.\n\n"
            f"<i>Сообщение будет переслано всем подписчикам этой категории.</i>",
            reply_markup=keyboard
        )
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=title,
                callback_data=f"notif_cat_{key}"
            )] for key, title in NOTIFICATION_CATEGORIES.items()
        ] + [[InlineKeyboardButton(text="❌ Отмена", callback_data="notif_cancel")]]
    )
    
    await message.answer(
        "📢 <b>Панель отправки уведомлений</b>\n\n"
        "Выберите категорию уведомления, которое хотите отправить:\n\n"
        "После выбора категории вы сможете отправить сообщение, "
        f"которое получат все участники, подписанные на эту категорию.\n\n"
        f"💡 <i>Вы можете отправить текст, фото, видео, документы, голосовые сообщения, стикеры и другие типы сообщений. "
        f"Все форматирование будет сохранено.</i>",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("notif_cat_"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    allowed, user_role = is_allowed_to_send_notifications(user_id)
    
    if not allowed:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    category_key = callback.data.replace("notif_cat_", "")
    category_title = NOTIFICATION_CATEGORIES.get(category_key, "Неизвестная категория")
    
    await state.update_data(notification_category=category_key)
    await state.set_state(NotificationStates.waiting_for_message)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="❌ Отмена", callback_data="notif_cancel")
        ]]
    )
    
    await callback.message.edit_text(
        f"📝 <b>Отправка уведомления</b>\n\n"
        f"Категория: <b>{category_title}</b>\n\n"
        f"Теперь отправьте сообщение, которое нужно разослать участникам.\n\n"
        f"Вы можете отправить любой тип сообщения, и оно будет переслано "
        f"с сохранением всего оригинального оформления.\n\n"
        f"<i>Сообщение будет переслано всем подписчикам этой категории.</i>",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "notif_cancel")
async def cancel_notification(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Отправка уведомления отменена.")
    await state.clear()
    await callback.answer()


@router.message(NotificationStates.waiting_for_message)
async def process_notification_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    allowed, user_role = is_allowed_to_send_notifications(user_id)
    
    if not allowed:
        await state.clear()
        return
    
    data = await state.get_data()
    category_key = data.get('notification_category')
    category_title = NOTIFICATION_CATEGORIES.get(category_key, "Неизвестная категория")
    
    all_members = group_manager.get_all_members()
    
    subscribers = []
    for member_id, member_data in all_members.items():
        notifications = member_data.get('notifications', {})
        if notifications.get(category_key, False):
            subscribers.append(int(member_id))
    
    if not subscribers:
        await message.answer(
            f"⚠️ <b>Нет подписчиков</b>\n\n"
            f"Ни один участник не подписан на категорию «{category_title}».\n\n"
            f"Уведомление не было отправлено."
        )
        await state.clear()
        return
    
    await message.answer(
        f"⏳ <b>Отправка уведомления...</b>\n\n"
        f"Категория: <b>{category_title}</b>\n"
        f"Подписчиков: <b>{len(subscribers)}</b>"
    )
    
    success_count = 0
    failed_count = 0
    
    for subscriber_id in subscribers:
        if subscriber_id == user_id:
            continue
        
        try:
            notification_header = (
                f"📢 <b>Уведомление: {category_title}</b>\n"
                f"{'─' * 30}"
            )
            await message.bot.send_message(
                subscriber_id,
                notification_header,
                parse_mode="HTML"
            )
            
            await message.bot.forward_message(
                chat_id=subscriber_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            
            success_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Ошибка отправки уведомления пользователю {subscriber_id}: {e}")
    
    report_text = (
        f"✅ <b>Уведомление отправлено</b>\n\n"
        f"Категория: <b>{category_title}</b>\n"
        f"Успешно доставлено: <b>{success_count}</b>\n"
    )
    
    if failed_count > 0:
        report_text += f"Не удалось доставить: <b>{failed_count}</b>\n"
    
    await message.answer(report_text)
    await state.clear()
