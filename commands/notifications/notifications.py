from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Создаем роутер для настроек уведомлений
router = Router()

# Хранилище для состояния уведомлений пользователей (временно в памяти)
# Структура: {user_id: {notification_type: bool}}
user_notifications = {}

# Типы уведомлений
NOTIFICATION_TYPES = {
    "bot_updates": "Обновление бота",
    "control_works": "Новые контрольные мероприятия",
    "homework": "Новые домашки",
    "proforg": "Профорг",
    "schedule_changes": "Изменения в расписании"
}


def get_user_notifications(user_id: int) -> dict:
    """Получить настройки уведомлений пользователя"""
    if user_id not in user_notifications:
        # По умолчанию все уведомления включены
        user_notifications[user_id] = {key: True for key in NOTIFICATION_TYPES.keys()}
    return user_notifications[user_id]


def toggle_notification(user_id: int, notification_type: str) -> bool:
    """Переключить уведомление"""
    notifications = get_user_notifications(user_id)
    notifications[notification_type] = not notifications[notification_type]
    return notifications[notification_type]


def toggle_all_notifications(user_id: int, enable: bool):
    """Включить/выключить все уведомления"""
    notifications = get_user_notifications(user_id)
    for key in notifications:
        notifications[key] = enable


def get_notifications_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Создать клавиатуру настроек уведомлений"""
    notifications = get_user_notifications(user_id)
    
    # Создаем кнопки для каждого типа уведомлений
    buttons = []
    for key, title in NOTIFICATION_TYPES.items():
        status = "🟢" if notifications[key] else "🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {title}",
                callback_data=f"toggle_{key}"
            )
        ])
    
    # Проверяем, все ли уведомления включены или выключены
    all_enabled = all(notifications.values())
    all_disabled = not any(notifications.values())
    
    # Кнопка включить/выключить все
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
        # Показываем обе кнопки, если частично включены
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
    
    # Кнопка "Вернуться назад"
    buttons.append([
        InlineKeyboardButton(text="⬅️ Вернуться назад", callback_data="back_to_start")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "notifications_menu")
async def show_notifications_menu(callback: CallbackQuery):
    """Показать меню настроек уведомлений"""
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
    """Обработчик переключения уведомлений"""
    user_id = callback.from_user.id
    
    # Определяем, что переключаем
    if callback.data == "toggle_all_on":
        toggle_all_notifications(user_id, True)
        await callback.answer("✅ Все уведомления включены")
    elif callback.data == "toggle_all_off":
        toggle_all_notifications(user_id, False)
        await callback.answer("❌ Все уведомления выключены")
    else:
        # Переключаем конкретное уведомление
        notification_type = callback.data.replace("toggle_", "")
        new_state = toggle_notification(user_id, notification_type)
        status = "включено" if new_state else "выключено"
        await callback.answer(f"Уведомление {status}")
    
    # Обновляем клавиатуру
    keyboard = get_notifications_keyboard(user_id)
    await callback.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    """Вернуться к стартовому сообщению"""
    user_name = callback.from_user.first_name
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔔 Настройки уведомлений", callback_data="notifications_menu")]
        ]
    )
    
    await callback.message.edit_text(
        f"👋 <b>Привет, {user_name}!</b>\n\n"
        f"Я бот для вашей группы в институте.\n"
        f"Используй /help чтобы узнать список доступных команд.\n\n"
        f"💡 <i>Команды работают только в личных сообщениях!</i>",
        reply_markup=keyboard
    )
    await callback.answer()
