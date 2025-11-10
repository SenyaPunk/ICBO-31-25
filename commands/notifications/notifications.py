from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from commands.group.group_manager import group_manager

router = Router()

NOTIFICATION_TYPES = {
    "bot_updates": "Обновление бота",
    "control_works": "Новые контрольные мероприятия",
    "homework": "Новые домашки",
    "proforg": "Профорг",
    "schedule_changes": "Изменения в расписании"
}


def get_user_notifications(user_id: int) -> dict:
    member = group_manager.get_member(user_id)
    if member and "notifications" in member:
        return member["notifications"]
    return {key: True for key in NOTIFICATION_TYPES.keys()}


def toggle_notification(user_id: int, notification_type: str) -> bool:
    notifications = get_user_notifications(user_id)
    notifications[notification_type] = not notifications[notification_type]
    group_manager.update_member(user_id, notifications=notifications)
    return notifications[notification_type]


def toggle_all_notifications(user_id: int, enable: bool):
    notifications = get_user_notifications(user_id)
    for key in notifications:
        notifications[key] = enable
    group_manager.update_member(user_id, notifications=notifications)


def get_notifications_keyboard(user_id: int) -> InlineKeyboardMarkup:
    notifications = get_user_notifications(user_id)
    
    buttons = []
    for key, title in NOTIFICATION_TYPES.items():
        status = "🟢" if notifications[key] else "🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {title}",
                callback_data=f"toggle_{key}"
            )
        ])
    
    all_enabled = all(notifications.values())
    all_disabled = not any(notifications.values())
    
    if all_enabled:
        buttons.append([
            InlineKeyboardButton(
                text="🔴 Отключить все уведомления",
                callback_data="toggle_all_off"
            )
        ])
    elif all_disabled:
        buttons.append([
            InlineKeyboardButton(
                text="🟢 Включить все уведомления",
                callback_data="toggle_all_on"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="🟢 Включить все",
                callback_data="toggle_all_on"
            ),
            InlineKeyboardButton(
                text="🔴 Выключить все",
                callback_data="toggle_all_off"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "notifications_menu")
async def show_notifications_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    keyboard = get_notifications_keyboard(user_id)
    
    await callback.message.edit_text(
        "🔔 <b>Настройки уведомлений</b>\n\n"
        "Выберите, какие уведомления вы хотите получать:\n\n"
        "🟢 - уведомление <b>включено</b>\n"
        "🔴 - уведомление <b>выключено</b>",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_"))
async def toggle_notification_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if callback.data == "toggle_all_on":
        toggle_all_notifications(user_id, True)
        await callback.answer("✅ Все уведомления включены")
    elif callback.data == "toggle_all_off":
        toggle_all_notifications(user_id, False)
        await callback.answer("❌ Все уведомления выключены")
    else:
        notification_type = callback.data.replace("toggle_", "")
        new_state = toggle_notification(user_id, notification_type)
        status = "включено" if new_state else "выключено"
        await callback.answer(f"Уведомление {status}")
    
    keyboard = get_notifications_keyboard(user_id)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
