from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from commands.group.group_manager import group_manager
from commands.notifications.notifications import get_notifications_keyboard, NOTIFICATION_TYPES

router = Router()


class RegistrationStates(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_name_confirmation = State()
    waiting_for_birth_date = State()
    waiting_for_notifications = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    if message.chat.type != ChatType.PRIVATE:
        return
    
    await state.clear()
    
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    member = group_manager.get_member(user_id)
    
    if member:
        await show_user_info(message, member, user_name)
    else:
        await message.answer(
            f"👋 <b>Добро пожаловать, {user_name}!</b>\n\n"
            f"Я бот для вашей учебной группы в институте.\n\n"
            f"Давайте познакомимся! Для начала укажите ваше <b>полное ФИО</b>.\n\n"
            f"Например: <code>Иванов Иван Иванович</code>"
        )
        await state.set_state(RegistrationStates.waiting_for_full_name)


async def show_user_info(message_or_callback, member: dict, user_name: str):
    role_emoji = {
        "Староста": "👔",
        "Зам старосты": "👔",
        "Профорг": "👔",
        "Участник": "🎓",
        "Гость": "👤"
    }
    
    notifications = member.get("notifications", {})
    enabled_count = sum(1 for v in notifications.values() if v)
    total_count = len(notifications)
    notifications_status = f"✅ Включено {enabled_count}/{total_count}"
    
    info_text = (
        f"👋 <b>Привет, {user_name}!</b>\n\n"
        f"📋 <b>Ваша информация:</b>\n\n"
        f"👤 <b>ФИО:</b> {member['full_name']}\n"
        f"🎂 <b>Дата рождения:</b> {member['birth_date']}\n"
        f"{role_emoji.get(member['role'], '🎓')} <b>Роль:</b> {member['role']}\n"
        f"🔔 <b>Уведомления:</b> {notifications_status}\n\n"
        f"💡 <i>Изменить данные может только создатель бота.</i>\n"
        f"Используй /help для списка команд."
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="🔔 Настройки уведомлений", callback_data="notifications_menu")
        ]]
    )
    
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(info_text, reply_markup=keyboard)
    else:
        await message_or_callback.message.edit_text(info_text, reply_markup=keyboard)


@router.callback_query(F.data == "notifications_menu")
async def show_notifications_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    member = group_manager.get_member(user_id)
    
    if not member:
        await callback.answer("❌ Вы не зарегистрированы!", show_alert=True)
        return
    
    notifications = member.get("notifications", {})
    keyboard = get_notifications_keyboard_with_back(notifications)
    
    enabled_count = sum(1 for v in notifications.values() if v)
    total_count = len(notifications)
    
    await callback.message.edit_text(
        f"🔔 <b>Настройки уведомлений</b>\n\n"
        f"Выберите, какие уведомления вы хотите получать:\n\n"
        f"🟢 - уведомление <b>включено</b>\n"
        f"🔴 - уведомление <b>выключено</b>\n\n"
        f"Активно: {enabled_count}/{total_count}",
        reply_markup=keyboard
    )
    await callback.answer()


def get_notifications_keyboard_with_back(notifications: dict) -> InlineKeyboardMarkup:
    buttons = []
    for key, title in NOTIFICATION_TYPES.items():
        status = "🟢" if notifications.get(key, False) else "🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {title}",
                callback_data=f"start_toggle_{key}"
            )
        ])
    
    all_enabled = all(notifications.values())
    all_disabled = not any(notifications.values())
    
    if all_enabled:
        buttons.append([
            InlineKeyboardButton(
                text="🔴 Отключить все",
                callback_data="start_toggle_all_off"
            )
        ])
    elif all_disabled:
        buttons.append([
            InlineKeyboardButton(
                text="🟢 Включить все",
                callback_data="start_toggle_all_on"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="🟢 Включить все",
                callback_data="start_toggle_all_on"
            ),
            InlineKeyboardButton(
                text="🔴 Выключить все",
                callback_data="start_toggle_all_off"
            )
        ])
    
    # Кнопка "Назад"
    buttons.append([
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="start_back_to_info"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("start_toggle_"))
async def toggle_notification_from_start(callback: CallbackQuery):
    user_id = callback.from_user.id
    member = group_manager.get_member(user_id)
    
    if not member:
        await callback.answer("❌ Вы не зарегистрированы!", show_alert=True)
        return
    
    notifications = member.get("notifications", {})
    
    if callback.data == "start_toggle_all_on":
        for key in NOTIFICATION_TYPES.keys():
            notifications[key] = True
        group_manager.update_member(user_id, notifications=notifications)
        await callback.answer("✅ Все уведомления включены")
    elif callback.data == "start_toggle_all_off":
        for key in NOTIFICATION_TYPES.keys():
            notifications[key] = False
        group_manager.update_member(user_id, notifications=notifications)
        await callback.answer("❌ Все уведомления выключены")
    else:
        notification_type = callback.data.replace("start_toggle_", "")
        notifications[notification_type] = not notifications.get(notification_type, False)
        group_manager.update_member(user_id, notifications=notifications)
        status = "включено" if notifications[notification_type] else "выключено"
        await callback.answer(f"Уведомление {status}")
    
    keyboard = get_notifications_keyboard_with_back(notifications)
    enabled_count = sum(1 for v in notifications.values() if v)
    total_count = len(notifications)
    
    await callback.message.edit_text(
        f"🔔 <b>Настройки уведомлений</b>\n\n"
        f"Выберите, какие уведомления вы хотите получать:\n\n"
        f"🟢 - уведомление <b>включено</b>\n"
        f"🔴 - уведомление <b>выключено</b>\n\n"
        f"Активно: {enabled_count}/{total_count}",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "start_back_to_info")
async def back_to_user_info(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    member = group_manager.get_member(user_id)
    
    if not member:
        await callback.answer("❌ Вы не зарегистрированы!", show_alert=True)
        return
    
    await show_user_info(callback, member, user_name)
    await callback.answer()


@router.message(RegistrationStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    """Обработка ввода ФИО"""
    full_name = message.text.strip()
    
    if len(full_name.split()) < 2:
        await message.answer(
            "❌ Пожалуйста, введите полное ФИО (Фамилия Имя Отчество).\n\n"
            "Например: <code>Иванов Иван Иванович</code>"
        )
        return
    
    all_members = group_manager.get_all_members()
    for member_id, member_data in all_members.items():
        if normalize_name(member_data['full_name']) == normalize_name(full_name):
            await message.answer(
                f"❌ <b>Ошибка регистрации!</b>\n\n"
                f"Пользователь с ФИО <b>{member_data['full_name']}</b> уже зарегистрирован в боте.\n\n"
                f"Если это вы, обратитесь к создателю бота для восстановления доступа.\n"
                f"Если это не вы, проверьте правильность написания вашего ФИО."
            )
            return
    
    found_in_group = check_name_in_group_list(full_name)
    
    await state.update_data(full_name=full_name)
    
    if found_in_group:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, это я", callback_data="confirm_name_yes")],
            [InlineKeyboardButton(text="❌ Нет, ввести заново", callback_data="confirm_name_no")]
        ])
        
        await message.answer(
            f"🔍 В списке группы найден пользователь:\n"
            f"<b>{full_name}</b>\n\n"
            f"Это вы?",
            reply_markup=keyboard
        )
        await state.set_state(RegistrationStates.waiting_for_name_confirmation)
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, зарегистрироваться как Гость", callback_data="register_as_guest")],
            [InlineKeyboardButton(text="❌ Нет, ввести ФИО заново", callback_data="confirm_name_no")]
        ])
        
        await message.answer(
            f"⚠️ <b>Внимание!</b>\n\n"
            f"Пользователь с ФИО <b>{full_name}</b> не найден в списке группы.\n\n"
            f"Вы можете зарегистрироваться как <b>Гость</b>.\n"
            f"Гости получают ограниченный доступ к функциям бота.\n\n"
            f"Продолжить регистрацию как Гость?",
            reply_markup=keyboard
        )
        await state.set_state(RegistrationStates.waiting_for_name_confirmation)


def normalize_name(name: str) -> str:
    return " ".join(name.lower().split())


def check_name_in_group_list(full_name: str) -> bool:
    group_list = [
        "Александров Максим Сергеевич",
        "Алехин Алекс Юльевич",
        "Баннов Артемий Михайлович",
        "Бицуев Тембулат Михайлович",
        "Блохин Фёдор Александрович",
        "Буджак Никита Николаевич",
        "Васильева Кристина Викторовна",
        "Жарикова Жанна Евгеньевна",
        "Кириллов Максим Владимирович",
        "Киселёва Ева Александровна",
        "Ко Джун",
        "Козлов Николай Антонович",
        "Кравчук Валентин Антонович",
        "Кубинский Арсений Игоревич",
        "Кульжанов Жан Ерболатович",
        "Левшин Никита Павлович",
        "Леонтьев Михаил Андреевич",
        "Липатова Мария Алексеевна",
        "Лисичина Вера Павловна",
        "Лобачев Фёдор Максимович",
        "Манаширов Марк Шавадисович",
        "Миронов Ярослав Игоревич",
        "Саркисян Нарек Каренович",
        "Скрипник Анжелика Петровна",
        "Судариков Владимир Владимирович",
        "Тимонин Максим Алексеевич",
        "Шевцов Захар Павлович"
    ]
    
    normalized_input = normalize_name(full_name)
    
    for name in group_list:
        if normalize_name(name) == normalized_input:
            return True
    
    return False


@router.callback_query(F.data == "confirm_name_yes", RegistrationStates.waiting_for_name_confirmation)
async def confirm_name_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    full_name = data.get("full_name")
    
    await callback.message.edit_text(
        f"✅ ФИО подтверждено: <b>{full_name}</b>\n\n"
        f"Теперь укажите вашу <b>дату рождения</b> в формате ДД.ММ.ГГГГ\n\n"
        f"Например: <code>15.03.2005</code>"
    )
    await state.set_state(RegistrationStates.waiting_for_birth_date)
    await callback.answer()


@router.callback_query(F.data == "register_as_guest", RegistrationStates.waiting_for_name_confirmation)
async def register_as_guest(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    full_name = data.get("full_name")
    
    await state.update_data(is_guest=True)
    
    await callback.message.edit_text(
        f"✅ ФИО принято: <b>{full_name}</b>\n"
        f"👤 Роль: <b>Гость</b>\n\n"
        f"Теперь укажите вашу <b>дату рождения</b> в формате ДД.ММ.ГГГГ\n\n"
        f"Например: <code>15.03.2005</code>"
    )
    await state.set_state(RegistrationStates.waiting_for_birth_date)
    await callback.answer()


@router.callback_query(F.data == "confirm_name_no", RegistrationStates.waiting_for_name_confirmation)
async def confirm_name_no(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        f"✏️ Хорошо, введите ваше <b>полное ФИО</b> заново.\n\n"
        f"Например: <code>Иванов Иван Иванович</code>"
    )
    await state.set_state(RegistrationStates.waiting_for_full_name)
    await callback.answer()


@router.message(RegistrationStates.waiting_for_birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    birth_date = message.text.strip()
    
    import re
    date_pattern = r'^\d{2}\.\d{2}\.\d{4}$'
    
    if not re.match(date_pattern, birth_date):
        await message.answer(
            "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ\n\n"
            "Например: <code>15.03.2005</code>"
        )
        return
    
    try:
        from datetime import datetime
        day, month, year = map(int, birth_date.split('.'))
        datetime(year, month, day)
    except ValueError:
        await message.answer(
            "❌ Указана некорректная дата. Проверьте правильность ввода.\n\n"
            "Например: <code>15.03.2005</code>"
        )
        return
    
    await state.update_data(birth_date=birth_date)
    
    temp_notifications = {key: True for key in NOTIFICATION_TYPES.keys()}
    await state.update_data(temp_notifications=temp_notifications)
    
    keyboard = get_registration_notifications_keyboard(temp_notifications)
    
    await message.answer(
        f"✅ Дата рождения принята: <b>{birth_date}</b>\n\n"
        f"🔔 <b>Настройка уведомлений</b>\n\n"
        f"Выберите, какие уведомления вы хотите получать:\n\n"
        f"🟢 - уведомление <b>включено</b>\n"
        f"🔴 - уведомление <b>выключено</b>\n\n"
        f"После настройки нажмите <b>\"Завершить регистрацию\"</b>",
        reply_markup=keyboard
    )
    await state.set_state(RegistrationStates.waiting_for_notifications)


def get_registration_notifications_keyboard(notifications: dict) -> InlineKeyboardMarkup:
    buttons = []
    for key, title in NOTIFICATION_TYPES.items():
        status = "🟢" if notifications[key] else "🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {title}",
                callback_data=f"reg_toggle_{key}"
            )
        ])
    
    all_enabled = all(notifications.values())
    all_disabled = not any(notifications.values())
    
    if all_enabled:
        buttons.append([
            InlineKeyboardButton(
                text="🔴 Отключить все",
                callback_data="reg_toggle_all_off"
            )
        ])
    elif all_disabled:
        buttons.append([
            InlineKeyboardButton(
                text="🟢 Включить все",
                callback_data="reg_toggle_all_on"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="🟢 Включить все",
                callback_data="reg_toggle_all_on"
            ),
            InlineKeyboardButton(
                text="🔴 Выключить все",
                callback_data="reg_toggle_all_off"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text="✅ Завершить регистрацию",
            callback_data="reg_finish"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("reg_toggle_"), RegistrationStates.waiting_for_notifications)
async def toggle_registration_notification(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    temp_notifications = data.get("temp_notifications", {})
    
    if callback.data == "reg_toggle_all_on":
        for key in temp_notifications:
            temp_notifications[key] = True
        await callback.answer("✅ Все уведомления включены")
    elif callback.data == "reg_toggle_all_off":
        for key in temp_notifications:
            temp_notifications[key] = False
        await callback.answer("❌ Все уведомления выключены")
    else:
        notification_type = callback.data.replace("reg_toggle_", "")
        temp_notifications[notification_type] = not temp_notifications[notification_type]
        status = "включено" if temp_notifications[notification_type] else "выключено"
        await callback.answer(f"Уведомление {status}")
    
    await state.update_data(temp_notifications=temp_notifications)
    keyboard = get_registration_notifications_keyboard(temp_notifications)
    await callback.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(F.data == "reg_finish", RegistrationStates.waiting_for_notifications)
async def finish_registration(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    full_name = data.get("full_name")
    birth_date = data.get("birth_date")
    temp_notifications = data.get("temp_notifications", {})
    is_guest = data.get("is_guest", False)
    
    group_manager.add_member(
        user_id=callback.from_user.id,
        telegram_username=callback.from_user.username,
        full_name=full_name,
        birth_date=birth_date,
        notifications=temp_notifications,
        is_guest=is_guest
    )
    
    enabled_count = sum(1 for v in temp_notifications.values() if v)
    total_count = len(temp_notifications)
    
    role_info = "\n🎭 <b>Роль:</b> Гость" if is_guest else ""
    
    await callback.message.edit_text(
        f"🎉 <b>Регистрация завершена!</b>\n\n"
        f"📋 <b>Ваши данные:</b>\n"
        f"👤 <b>ФИО:</b> {full_name}\n"
        f"🎂 <b>Дата рождения:</b> {birth_date}{role_info}\n"
        f"🔔 <b>Уведомления:</b> включено {enabled_count}/{total_count}\n\n"
        f"Теперь вы можете использовать все функции бота!\n"
        f"Используйте /help для списка команд."
    )
    
    await state.clear()
    await callback.answer("✅ Регистрация успешно завершена!")
