"""
Команды администратора для управления данными участников
"""
import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

from commands.group.group_manager import group_manager, Role

load_dotenv()

router = Router()

ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))


class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_field_choice = State()
    waiting_for_new_value = State()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для использования этой команды.")
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✏️ Изменить данные участника", callback_data="admin_edit_member")],
            [InlineKeyboardButton(text="👥 Список всех участников", callback_data="admin_list_members")],
            [InlineKeyboardButton(text="👔 Управление ролями", callback_data="admin_roles")]
        ]
    )
    
    await message.answer(
        "👨‍💼 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "admin_edit_member")
async def admin_edit_member(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "✏️ <b>Редактирование данных участника</b>\n\n"
        "Введите ID пользователя, данные которого хотите изменить.\n\n"
        "💡 Пользователь может узнать свой ID, отправив команду /myid боту."
    )
    await state.set_state(AdminStates.waiting_for_user_id)
    await callback.answer()


@router.message(AdminStates.waiting_for_user_id)
async def process_user_id_for_edit(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    try:
        user_id = int(message.text.strip())
        member = group_manager.get_member(user_id)
        
        if not member:
            await message.answer(
                f"❌ Участник с ID {user_id} не найден в базе.\n\n"
                "Убедитесь, что пользователь уже зарегистрирован."
            )
            return
        
        await state.update_data(edit_user_id=user_id)
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="👤 ФИО", callback_data="edit_full_name")],
                [InlineKeyboardButton(text="🎂 Дата рождения", callback_data="edit_birth_date")],
                [InlineKeyboardButton(text="🔔 Уведомления", callback_data="edit_notifications")],
                [InlineKeyboardButton(text="👔 Роль", callback_data="edit_role")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="edit_cancel")]
            ]
        )
        
        notifications = member.get('notifications', {})
        enabled_count = sum(1 for v in notifications.values() if v)
        total_count = len(notifications)
        notifications_status = f"Включено {enabled_count}/{total_count}"
        
        await message.answer(
            f"📋 <b>Данные участника:</b>\n\n"
            f"👤 <b>ФИО:</b> {member['full_name']}\n"
            f"🎂 <b>Дата рождения:</b> {member['birth_date']}\n"
            f"🔔 <b>Уведомления:</b> {notifications_status}\n"
            f"👔 <b>Роль:</b> {member['role']}\n\n"
            f"Что вы хотите изменить?",
            reply_markup=keyboard
        )
        await state.set_state(AdminStates.waiting_for_field_choice)
        
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите числовой ID пользователя.")


@router.callback_query(F.data == "edit_full_name", AdminStates.waiting_for_field_choice)
async def edit_full_name_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await state.update_data(edit_field="full_name")
    await callback.message.edit_text(
        "Введите новое ФИО:\n\nНапример: <code>Петров Петр Петрович</code>"
    )
    await state.set_state(AdminStates.waiting_for_new_value)
    await callback.answer()


@router.callback_query(F.data == "edit_birth_date", AdminStates.waiting_for_field_choice)
async def edit_birth_date_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await state.update_data(edit_field="birth_date")
    await callback.message.edit_text(
        "Введите новую дату рождения в формате ДД.ММ.ГГГГ:\n\nНапример: <code>20.05.2005</code>"
    )
    await state.set_state(AdminStates.waiting_for_new_value)
    await callback.answer()


@router.callback_query(F.data == "edit_notifications", AdminStates.waiting_for_field_choice)
async def edit_notifications_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await state.update_data(edit_field="notifications")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Включить", callback_data="notif_on")],
            [InlineKeyboardButton(text="❌ Выключить", callback_data="notif_off")]
        ]
    )
    await callback.message.edit_text(
        "Выберите статус уведомлений:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "edit_role", AdminStates.waiting_for_field_choice)
async def edit_role_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await state.update_data(edit_field="role")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👔 Староста", callback_data="role_starosta")],
            [InlineKeyboardButton(text="👔 Зам старосты", callback_data="role_zam")],
            [InlineKeyboardButton(text="👔 Профорг", callback_data="role_proforg")],
            [InlineKeyboardButton(text="🎓 Участник", callback_data="role_participant")],
            [InlineKeyboardButton(text="👤 Гость", callback_data="role_guest")]
        ]
    )
    await callback.message.edit_text(
        "Выберите новую роль:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "edit_cancel", AdminStates.waiting_for_field_choice)
async def edit_cancel_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text("❌ Редактирование отменено.")
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("notif_"), AdminStates.waiting_for_field_choice)
async def process_notifications_choice(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    data = await state.get_data()
    user_id = data.get("edit_user_id")
    
    member = group_manager.get_member(user_id)
    notifications = member.get('notifications', {})
    
    notifications_enabled = callback.data == "notif_on"
    for key in notifications:
        notifications[key] = notifications_enabled
    
    group_manager.update_member(user_id, notifications=notifications)
    
    status = "включены" if notifications_enabled else "выключены"
    
    await callback.message.edit_text(
        f"✅ Уведомления успешно {status} для пользователя {user_id}\n\n"
        f"Пользователь получит уведомление об изменении."
    )
    
    try:
        await callback.bot.send_message(
            user_id,
            f"📝 Ваши данные были обновлены администратором.\n\n"
            f"🔔 Уведомления теперь {status}."
        )
    except:
        pass
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("role_"), AdminStates.waiting_for_field_choice)
async def process_role_choice(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    data = await state.get_data()
    user_id = data.get("edit_user_id")
    
    role_map = {
        "role_starosta": Role.STAROSTA,
        "role_zam": Role.ZAM_STAROSTA,
        "role_proforg": Role.PROFORG,
        "role_participant": Role.PARTICIPANT,
        "role_guest": Role.GUEST
    }
    
    new_role = role_map[callback.data]
    group_manager.update_member(user_id, role=new_role)
    
    await callback.message.edit_text(
        f"✅ Роль успешно изменена на <b>{new_role.value}</b> для пользователя {user_id}\n\n"
        f"Пользователь получит уведомление об изменении."
    )
    
    try:
        await callback.bot.send_message(
            user_id,
            f"📝 Ваши данные были обновлены администратором.\n\n"
            f"👔 Ваша новая роль: <b>{new_role.value}</b>"
        )
    except:
        pass
    
    await state.clear()
    await callback.answer()


@router.message(AdminStates.waiting_for_new_value)
async def process_new_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    
    data = await state.get_data()
    user_id = data.get("edit_user_id")
    field = data.get("edit_field")
    new_value = message.text.strip()
    
    if field == "full_name":
        if len(new_value.split()) < 2:
            await message.answer(
                "❌ ФИО должно содержать минимум 2 слова.\n"
                "Попробуйте снова."
            )
            return
        group_manager.update_member(user_id, full_name=new_value)
        field_name = "ФИО"
        
    elif field == "birth_date":
        import re
        if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', new_value):
            await message.answer(
                "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ\n"
                "Попробуйте снова."
            )
            return
        
        try:
            from datetime import datetime
            day, month, year = map(int, new_value.split('.'))
            datetime(year, month, day)
        except ValueError:
            await message.answer(
                "❌ Некорректная дата. Проверьте правильность.\n"
                "Попробуйте снова."
            )
            return
        
        group_manager.update_member(user_id, birth_date=new_value)
        field_name = "Дата рождения"
    
    await message.answer(
        f"✅ {field_name} успешно обновлено для пользователя {user_id}\n\n"
        f"Новое значение: <b>{new_value}</b>\n\n"
        f"Пользователь получит уведомление об изменении."
    )
    
    try:
        await message.bot.send_message(
            user_id,
            f"📝 Ваши данные были обновлены администратором.\n\n"
            f"<b>{field_name}:</b> {new_value}"
        )
    except:
        pass
    
    await state.clear()


@router.callback_query(F.data == "admin_list_members")
async def admin_list_members(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    members = group_manager.get_all_members()
    
    if not members:
        await callback.message.edit_text("📋 База участников пуста.")
        await callback.answer()
        return
    
    by_role = {}
    for member in members.values():
        role = member['role']
        if role not in by_role:
            by_role[role] = []
        by_role[role].append(member)
    
    text = "👥 <b>Список всех участников:</b>\n\n"
    
    role_order = ["Староста", "Зам старосты", "Профорг", "Участник", "Гость"]
    
    for role in role_order:
        if role in by_role:
            text += f"<b>{role}:</b>\n"
            for member in by_role[role]:
                text += f"  • {member['full_name']} (ID: <code>{member['user_id']}</code>)\n"
            text += "\n"
    
    text += f"<b>Всего участников:</b> {len(members)}"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin")
        ]]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_roles")
async def admin_roles(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    starosta = group_manager.get_members_by_role(Role.STAROSTA)
    zam = group_manager.get_members_by_role(Role.ZAM_STAROSTA)
    proforg = group_manager.get_members_by_role(Role.PROFORG)
    
    text = "👔 <b>Управление группой:</b>\n\n"
    
    text += "<b>Староста:</b>\n"
    if starosta:
        text += f"  • {starosta[0]['full_name']} (ID: <code>{starosta[0]['user_id']}</code>)\n"
    else:
        text += "  • Не назначен\n"
    
    text += "\n<b>Зам старосты:</b>\n"
    if zam:
        text += f"  • {zam[0]['full_name']} (ID: <code>{zam[0]['user_id']}</code>)\n"
    else:
        text += "  • Не назначен\n"
    
    text += "\n<b>Профорг:</b>\n"
    if proforg:
        text += f"  • {proforg[0]['full_name']} (ID: <code>{proforg[0]['user_id']}</code>)\n"
    else:
        text += "  • Не назначен\n"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin")
        ]]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✏️ Изменить данные участника", callback_data="admin_edit_member")],
            [InlineKeyboardButton(text="👥 Список всех участников", callback_data="admin_list_members")],
            [InlineKeyboardButton(text="👔 Управление ролями", callback_data="admin_roles")]
        ]
    )
    
    await callback.message.edit_text(
        "👨‍💼 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(
        f"🆔 Ваш Telegram ID: <code>{message.from_user.id}</code>\n\n"
        f"💡 Нажмите на ID, чтобы скопировать."
    )
