

import logging
import re
from datetime import date, datetime, timedelta
from typing import Optional

from aiogram import Router, F
from aiogram.types import (
    Message, 
    CallbackQuery, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatType  
from dateutil import tz

from commands.group.group_manager import group_manager
from commands.homework.homework_storage import HomeworkStorage
from commands.schedule.schedule_storage import ScheduleStorage, ALL_SUBJECTS
from utils.calendar_keyboard import (
    CalendarKeyboard, format_date_ru
)

router = Router()
logger = logging.getLogger(__name__)

WEEKDAYS_RU = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]

homework_storage = HomeworkStorage()
schedule_storage = ScheduleStorage()

quick_hw_pending = {}

quick_homework_calendar = CalendarKeyboard(callback_prefix="qhw_cal")

class HomeworkStates(StatesGroup):
    selecting_subject = State()
    entering_task = State()
    selecting_date = State()
    confirming = State()


class ControlMeasureStates(StatesGroup):
    selecting_subject = State()
    entering_description = State()
    selecting_date = State()
    confirming = State()


class QuickHomeworkStates(StatesGroup):
    entering_task = State()
    selecting_date = State()
    confirming = State()


def get_headman_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Добавить ДЗ"),
                KeyboardButton(text="📋 Добавить КМ")
            ],
            [
                KeyboardButton(text="📚 Текущие ДЗ"),
                KeyboardButton(text="📊 Текущие КМ")
            ]
        ],
        resize_keyboard=True,
        is_persistent=True
    )


def create_subjects_keyboard(page: int = 0, items_per_page: int = 8, prefix: str = "hw") -> InlineKeyboardMarkup:
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_subjects = ALL_SUBJECTS[start_idx:end_idx]
    
    buttons = []
    for subject in current_subjects:
        subject_idx = ALL_SUBJECTS.index(subject)
        buttons.append([InlineKeyboardButton(
            text=subject,
            callback_data=f"{prefix}_subj:{subject_idx}"
        )])
    
    nav_buttons = []
    total_pages = (len(ALL_SUBJECTS) + items_per_page - 1) // items_per_page
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"{prefix}_page:{page - 1}"
        ))
    
    nav_buttons.append(InlineKeyboardButton(
        text=f"{page + 1}/{total_pages}",
        callback_data=f"{prefix}_page_info"
    ))
    
    if end_idx < len(ALL_SUBJECTS):
        nav_buttons.append(InlineKeyboardButton(
            text="Вперед ➡️",
            callback_data=f"{prefix}_page:{page + 1}"
        ))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(
        text="❌ Отмена",
        callback_data=f"{prefix}_cancel"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)



@router.message(Command("homework"))
async def cmd_homework(message: Message):
    homework_storage.reload_data()
    
    upcoming_hw = homework_storage.get_all_upcoming_homework()
    upcoming_km = homework_storage.get_all_upcoming_control_measures()
    
    text = "📚 <b>Домашние задания и контрольные мероприятия</b>\n\n"
    
    if not upcoming_hw and not upcoming_km:
        text += "🎉 На данный момент нет активных заданий!"
    else:
        if upcoming_hw:
            text += "📝 <b>Домашние задания:</b>\n\n"
            for hw_date, subject, tasks in upcoming_hw:
                date_str = format_date_ru(hw_date)
                text += f"📅 <b>{date_str}</b>\n"
                text += f"   📖 {subject}\n"
                for task in tasks:
                    text += f"      • {task}\n"
                text += "\n"
        
        if upcoming_km:
            text += "📋 <b>Контрольные мероприятия:</b>\n\n"
            for km_date, subject, descriptions in upcoming_km:
                date_str = format_date_ru(km_date)
                text += f"📅 <b>{date_str}</b>\n"
                text += f"   📖 {subject}\n"
                for desc in descriptions:
                    text += f"      ⚠️ {desc}\n"
                text += "\n"
    
    if is_headman_or_proforg(message.from_user.id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Добавить ДЗ", callback_data="start_add_hw"),
                InlineKeyboardButton(text="📋 Добавить КМ", callback_data="start_add_km")
            ],
            [
                InlineKeyboardButton(text="🗑 Управление", callback_data="manage_homework")
            ]
        ])
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(text, parse_mode="HTML")



@router.message(F.text == "📝 Добавить ДЗ")
async def handle_add_hw_button(message: Message, state: FSMContext):
    """Обработка кнопки 'Добавить ДЗ'."""
    if message.chat.type != ChatType.PRIVATE:
        return
    
    if not is_headman_or_proforg(message.from_user.id):
        await message.answer("⛔ Эта функция доступна только старосте и профоргу.")
        return
    
    await start_add_homework(message, state)


@router.message(F.text == "📋 Добавить КМ")
async def handle_add_km_button(message: Message, state: FSMContext):
    if message.chat.type != ChatType.PRIVATE:
        return
    
    if not is_headman_or_proforg(message.from_user.id):
        await message.answer("⛔ Эта функция доступна только старосте и профоргу.")
        return
    
    await start_add_control_measure(message, state)


@router.message(F.text == "📚 Текущие ДЗ")
async def handle_view_hw_button(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    
    await cmd_homework(message)


@router.message(F.text == "📊 Текущие КМ")
async def handle_view_km_button(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    
    homework_storage.reload_data()
    
    upcoming_km = homework_storage.get_all_upcoming_control_measures()
    
    text = "📋 <b>Контрольные мероприятия</b>\n\n"
    
    if not upcoming_km:
        text += "🎉 На данный момент нет запланированных КМ!"
    else:
        for km_date, subject, descriptions in upcoming_km:
            date_str = format_date_ru(km_date)
            text += f"📅 <b>{date_str}</b>\n"
            text += f"   📖 {subject}\n"
            for desc in descriptions:
                text += f"      ⚠️ {desc}\n"
            text += "\n"
    
    if is_headman_or_proforg(message.from_user.id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Добавить КМ", callback_data="start_add_km")],
            [InlineKeyboardButton(text="🗑 Управление КМ", callback_data="manage_km")]
        ])
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(text, parse_mode="HTML")



@router.callback_query(F.data == "start_add_hw")
async def callback_start_add_hw(callback: CallbackQuery, state: FSMContext):
    """Начать добавление ДЗ через inline-кнопку."""
    if not is_headman_or_proforg(callback.from_user.id):
        await callback.answer("⛔ Только для старосты!", show_alert=True)
        return
    
    await callback.answer()
    await start_add_homework(callback.message, state, edit=True)


@router.callback_query(F.data == "start_add_km")
async def callback_start_add_km(callback: CallbackQuery, state: FSMContext):
    if not is_headman_or_proforg(callback.from_user.id):
        await callback.answer("⛔ Только для старосты!", show_alert=True)
        return
    
    await callback.answer()
    await start_add_control_measure(callback.message, state, edit=True)



async def start_add_homework(message: Message, state: FSMContext, edit: bool = False):
    await state.set_state(HomeworkStates.selecting_subject)
    await state.update_data(current_page=0)
    
    keyboard = create_subjects_keyboard(page=0, prefix="hw")
    text = "📝 <b>Добавление домашнего задания</b>\n\n📚 Выберите предмет:"
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("hw_page:"), HomeworkStates.selecting_subject)
async def hw_page_navigation(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    await state.update_data(current_page=page)
    
    keyboard = create_subjects_keyboard(page=page, prefix="hw")
    await callback.message.edit_text(
        "📝 <b>Добавление домашнего задания</b>\n\n📚 Выберите предмет:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "hw_page_info")
async def hw_page_info(callback: CallbackQuery):
    await callback.answer("Текущая страница")


@router.callback_query(F.data.startswith("hw_subj:"), HomeworkStates.selecting_subject)
async def hw_select_subject(callback: CallbackQuery, state: FSMContext):
    subject_idx = int(callback.data.split(":")[1])
    
    if 0 <= subject_idx < len(ALL_SUBJECTS):
        subject = ALL_SUBJECTS[subject_idx]
        await state.update_data(subject=subject)
        await state.set_state(HomeworkStates.entering_task)
        
        await callback.message.edit_text(
            f"📝 <b>Добавление ДЗ</b>\n\n"
            f"📖 Предмет: <b>{subject}</b>\n\n"
            f"✏️ Отправьте текст домашнего задания:",
            parse_mode="HTML"
        )
        await callback.answer()
    else:
        await callback.answer("❌ Ошибка: предмет не найден", show_alert=True)


@router.callback_query(F.data == "hw_cancel")
async def hw_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Добавление ДЗ отменено.")
    await callback.answer()


@router.message(HomeworkStates.entering_task)
async def hw_receive_task(message: Message, state: FSMContext):
    task = message.text.strip()
    
    if not task:
        await message.answer("❌ Пожалуйста, введите текст задания.")
        return
    
    await state.update_data(task=task)
    await state.set_state(HomeworkStates.selecting_date)
    
    data = await state.get_data()
    subject = data.get("subject", "")
    
    calendar_kb = quick_homework_calendar.create_calendar()
    
    await message.answer(
        f"📝 <b>Добавление ДЗ</b>\n\n"
        f"📖 Предмет: <b>{subject}</b>\n"
        f"✏️ Задание: {task}\n\n"
        f"📅 Выберите дату, к которой нужно выполнить ДЗ:",
        reply_markup=calendar_kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("qhw_cal:"), HomeworkStates.selecting_date)
async def hw_calendar_callback(callback: CallbackQuery, state: FSMContext):
    action, selected_date, year, month = quick_homework_calendar.parse_callback(callback.data)
    
    if action == "ignore":
        await callback.answer()
        return
    
    if action == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Добавление ДЗ отменено.")
        await callback.answer()
        return
    
    if action in ["prev_month", "next_month", "prev_year", "next_year"]:
        calendar_kb = quick_homework_calendar.create_calendar(year=year, month=month)
        data = await state.get_data()
        
        await callback.message.edit_text(
            f"📝 <b>Добавление ДЗ</b>\n\n"
            f"📖 Предмет: <b>{data.get('subject', '')}</b>\n"
            f"✏️ Задание: {data.get('task', '')}\n\n"
            f"📅 Выберите дату, к которой нужно выполнить ДЗ:",
            reply_markup=calendar_kb,
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    if action in ["select", "today"]:
        await state.update_data(target_date=selected_date.isoformat())
        await state.set_state(HomeworkStates.confirming)
        
        data = await state.get_data()
        date_str = format_date_ru(selected_date)
        
        confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="hw_confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="hw_cancel_confirm")
            ]
        ])
        
        await callback.message.edit_text(
            f"📝 <b>Проверьте данные ДЗ:</b>\n\n"
            f"📅 <b>{date_str}</b>\n"
            f"📖 {data.get('subject', '')}\n"
            f"✏️ {data.get('task', '')}\n\n"
            f"Всё верно?",
            reply_markup=confirm_kb,
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data == "hw_confirm", HomeworkStates.confirming)
async def hw_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    target_date = date.fromisoformat(data.get("target_date"))
    subject = data.get("subject", "")
    task = data.get("task", "")
    
    success = homework_storage.add_homework(target_date, subject, task)
    
    await state.clear()
    
    if success:
        date_str = format_date_ru(target_date)
        await callback.message.edit_text(
            f"✅ <b>ДЗ успешно добавлено!</b>\n\n"
            f"📅 {date_str}\n"
            f"📖 {subject}\n"
            f"✏️ {task}",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("❌ Ошибка при сохранении ДЗ. Попробуйте еще раз.")
    
    await callback.answer()


@router.callback_query(F.data == "hw_cancel_confirm")
async def hw_cancel_confirm(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Добавление ДЗ отменено.")
    await callback.answer()



async def start_add_control_measure(message: Message, state: FSMContext, edit: bool = False):
    await state.set_state(ControlMeasureStates.selecting_subject)
    await state.update_data(current_page=0)
    
    keyboard = create_subjects_keyboard(page=0, prefix="km")
    text = "📋 <b>Добавление контрольного мероприятия</b>\n\n📚 Выберите предмет:"
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("km_page:"), ControlMeasureStates.selecting_subject)
async def km_page_navigation(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    await state.update_data(current_page=page)
    
    keyboard = create_subjects_keyboard(page=page, prefix="km")
    await callback.message.edit_text(
        "📋 <b>Добавление контрольного мероприятия</b>\n\n📚 Выберите предмет:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "km_page_info")
async def km_page_info(callback: CallbackQuery):
    await callback.answer("Текущая страница")


@router.callback_query(F.data.startswith("km_subj:"), ControlMeasureStates.selecting_subject)
async def km_select_subject(callback: CallbackQuery, state: FSMContext):
    subject_idx = int(callback.data.split(":")[1])
    
    if 0 <= subject_idx < len(ALL_SUBJECTS):
        subject = ALL_SUBJECTS[subject_idx]
        await state.update_data(subject=subject)
        await state.set_state(ControlMeasureStates.entering_description)
        
        await callback.message.edit_text(
            f"📋 <b>Добавление КМ</b>\n\n"
            f"📖 Предмет: <b>{subject}</b>\n\n"
            f"✏️ Отправьте описание контрольного мероприятия\n"
            f"(например: <i>Контрольная работа по теме 1-3</i>):",
            parse_mode="HTML"
        )
        await callback.answer()
    else:
        await callback.answer("❌ Ошибка: предмет не найден", show_alert=True)


@router.callback_query(F.data == "km_cancel")
async def km_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Добавление КМ отменено.")
    await callback.answer()


@router.message(ControlMeasureStates.entering_description)
async def km_receive_description(message: Message, state: FSMContext):
    description = message.text.strip()
    
    if not description:
        await message.answer("❌ Пожалуйста, введите описание КМ.")
        return
    
    await state.update_data(description=description)
    await state.set_state(ControlMeasureStates.selecting_date)
    
    data = await state.get_data()
    subject = data.get("subject", "")
    
    calendar_kb = quick_homework_calendar.create_calendar()
    
    await message.answer(
        f"📋 <b>Добавление КМ</b>\n\n"
        f"📖 Предмет: <b>{subject}</b>\n"
        f"📝 Описание: {description}\n\n"
        f"📅 Выберите дату проведения КМ:",
        reply_markup=calendar_kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("qhw_cal:"), ControlMeasureStates.selecting_date)
async def km_calendar_callback(callback: CallbackQuery, state: FSMContext):
    action, selected_date, year, month = quick_homework_calendar.parse_callback(callback.data)
    
    if action == "ignore":
        await callback.answer()
        return
    
    if action == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Добавление КМ отменено.")
        await callback.answer()
        return
    
    if action in ["prev_month", "next_month", "prev_year", "next_year"]:
        calendar_kb = quick_homework_calendar.create_calendar(year=year, month=month)
        data = await state.get_data()
        
        await callback.message.edit_text(
            f"📋 <b>Добавление КМ</b>\n\n"
            f"📖 Предмет: <b>{data.get('subject', '')}</b>\n"
            f"📝 Описание: {data.get('description', '')}\n\n"
            f"📅 Выберите дату проведения КМ:",
            reply_markup=calendar_kb,
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    if action in ["select", "today"]:
        await state.update_data(target_date=selected_date.isoformat())
        await state.set_state(ControlMeasureStates.confirming)
        
        data = await state.get_data()
        date_str = format_date_ru(selected_date)
        
        confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="km_confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="km_cancel_confirm")
            ]
        ])
        
        await callback.message.edit_text(
            f"📋 <b>Проверьте данные КМ:</b>\n\n"
            f"📅 <b>{date_str}</b>\n"
            f"📖 {data.get('subject', '')}\n"
            f"⚠️ {data.get('description', '')}\n\n"
            f"Всё верно?",
            reply_markup=confirm_kb,
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data == "km_confirm", ControlMeasureStates.confirming)
async def km_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    target_date = date.fromisoformat(data.get("target_date"))
    subject = data.get("subject", "")
    description = data.get("description", "")
    
    success = homework_storage.add_control_measure(target_date, subject, description)
    
    await state.clear()
    
    if success:
        date_str = format_date_ru(target_date)
        await callback.message.edit_text(
            f"✅ <b>КМ успешно добавлено!</b>\n\n"
            f"📅 {date_str}\n"
            f"📖 {subject}\n"
            f"⚠️ {description}",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("❌ Ошибка при сохранении КМ. Попробуйте еще раз.")
    
    await callback.answer()


@router.callback_query(F.data == "km_cancel_confirm")
async def km_cancel_confirm(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Добавление КМ отменено.")
    await callback.answer()



@router.callback_query(F.data == "manage_homework")
async def manage_homework(callback: CallbackQuery):
    if not is_headman_or_proforg(callback.from_user.id):
        await callback.answer("⛔ Только для старосты!", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Удалить ДЗ", callback_data="delete_hw_menu")],
        [InlineKeyboardButton(text="🗑 Удалить КМ", callback_data="delete_km_menu")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_homework")]
    ])
    
    await callback.message.edit_text(
        "🔧 <b>Управление домашними заданиями и КМ</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_homework")
async def back_to_homework(callback: CallbackQuery):
    homework_storage.reload_data()
    
    upcoming_hw = homework_storage.get_all_upcoming_homework()
    upcoming_km = homework_storage.get_all_upcoming_control_measures()
    
    text = "📚 <b>Домашние задания и контрольные мероприятия</b>\n\n"
    
    if not upcoming_hw and not upcoming_km:
        text += "🎉 На данный момент нет активных заданий!"
    else:
        if upcoming_hw:
            text += "📝 <b>Домашние задания:</b>\n\n"
            for hw_date, subject, tasks in upcoming_hw:
                date_str = format_date_ru(hw_date)
                text += f"📅 <b>{date_str}</b>\n"
                text += f"   📖 {subject}\n"
                for task in tasks:
                    text += f"      • {task}\n"
                text += "\n"
        
        if upcoming_km:
            text += "📋 <b>Контрольные мероприятия:</b>\n\n"
            for km_date, subject, descriptions in upcoming_km:
                date_str = format_date_ru(km_date)
                text += f"📅 <b>{date_str}</b>\n"
                text += f"   📖 {subject}\n"
                for desc in descriptions:
                    text += f"      ⚠️ {desc}\n"
                text += "\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Добавить ДЗ", callback_data="start_add_hw"),
            InlineKeyboardButton(text="📋 Добавить КМ", callback_data="start_add_km")
        ],
        [
            InlineKeyboardButton(text="🗑 Управление", callback_data="manage_homework")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "delete_hw_menu")
async def delete_hw_menu(callback: CallbackQuery):
    homework_storage.reload_data()
    upcoming = homework_storage.get_all_upcoming_homework()
    
    if not upcoming:
        await callback.answer("Нет ДЗ для удаления", show_alert=True)
        return
    
    buttons = []
    for i, (hw_date, subject, tasks) in enumerate(upcoming[:10]):  # Макс 10
        date_str = hw_date.strftime("%d.%m")
        short_subject = subject[:25] + "..." if len(subject) > 25 else subject
        buttons.append([InlineKeyboardButton(
            text=f"🗑 {date_str} - {short_subject}",
            callback_data=f"del_hw:{hw_date.isoformat()}:{subject[:40]}"
        )])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="manage_homework")])
    
    await callback.message.edit_text(
        "🗑 <b>Удаление домашнего задания</b>\n\n"
        "Выберите ДЗ для удаления:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("del_hw:"))
async def delete_hw_confirm(callback: CallbackQuery):
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    target_date = date.fromisoformat(parts[1])
    subject_partial = parts[2]
    
    homework_storage.reload_data()
    hw_data = homework_storage.get_homework_for_date(target_date)
    
    subject = None
    for subj in hw_data.keys():
        if subj.startswith(subject_partial) or subject_partial in subj:
            subject = subj
            break
    
    if subject and homework_storage.remove_homework(target_date, subject):
        await callback.answer("✅ ДЗ удалено!", show_alert=True)
        await delete_hw_menu(callback)
    else:
        await callback.answer("❌ Ошибка удаления", show_alert=True)


@router.callback_query(F.data == "delete_km_menu")
async def delete_km_menu(callback: CallbackQuery):
    homework_storage.reload_data()
    upcoming = homework_storage.get_all_upcoming_control_measures()
    
    if not upcoming:
        await callback.answer("Нет КМ для удаления", show_alert=True)
        return
    
    buttons = []
    for i, (km_date, subject, descriptions) in enumerate(upcoming[:10]):
        date_str = km_date.strftime("%d.%m")
        short_subject = subject[:25] + "..." if len(subject) > 25 else subject
        buttons.append([InlineKeyboardButton(
            text=f"🗑 {date_str} - {short_subject}",
            callback_data=f"del_km:{km_date.isoformat()}:{subject[:40]}"
        )])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="manage_homework")])
    
    await callback.message.edit_text(
        "🗑 <b>Удаление контрольного мероприятия</b>\n\n"
        "Выберите КМ для удаления:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("del_km:"))
async def delete_km_confirm(callback: CallbackQuery):
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    target_date = date.fromisoformat(parts[1])
    subject_partial = parts[2]
    
    homework_storage.reload_data()
    km_data = homework_storage.get_control_measures_for_date(target_date)
    
    subject = None
    for subj in km_data.keys():
        if subj.startswith(subject_partial) or subject_partial in subj:
            subject = subj
            break
    
    if subject and homework_storage.remove_control_measure(target_date, subject):
        await callback.answer("✅ КМ удалено!", show_alert=True)
        await delete_km_menu(callback)
    else:
        await callback.answer("❌ Ошибка удаления", show_alert=True)



@router.callback_query(F.data.startswith("quick_hw:"))
async def quick_add_homework_start(callback: CallbackQuery, state: FSMContext):
    try:
        
        parts = callback.data.split(":", 2)
        if len(parts) < 3:
            await callback.answer("❌ Ошибка: неверные данные", show_alert=True)
            return
        
        lesson_id = parts[1]
        subject = parts[2]
        
        message_info = schedule_storage.get_attendance_message_info(lesson_id)
        if message_info:
            lesson_start_str = message_info.get("lesson_start", "")
            break_minutes = message_info.get("break_minutes", 10)
            
            if lesson_start_str:
                try:
                    moscow_tz = tz.gettz("Europe/Moscow")
                    lesson_start = datetime.fromisoformat(lesson_start_str)
                    now = datetime.now(moscow_tz)
                    
                    # Лимит: 1.5 часа (90 минут) + перерыв
                    time_limit_minutes = 90 + break_minutes
                    deadline = lesson_start + timedelta(minutes=time_limit_minutes)
                    
                    if now > deadline:
                        await callback.answer(
                            f"⏰ Время для добавления ДЗ истекло.\n"
                            f"ДЗ можно было добавить до {deadline.strftime('%H:%M')}",
                            show_alert=True
                        )
                        return
                except Exception as e:
                    logger.error(f"Ошибка при проверке времени ДЗ: {e}")
        
        user_id = callback.from_user.id
        user_name = callback.from_user.first_name or "Участник"
        
        quick_hw_pending[user_id] = {
            "lesson_id": lesson_id,
            "subject": subject,
            "chat_id": callback.message.chat.id,
            "message_id": callback.message.message_id,
            "timestamp": datetime.now(tz.gettz("Europe/Moscow")).isoformat()
        }
        
        await callback.message.reply(
            f"📝 <b>{user_name}</b>, напишите домашнее задание для:\n"
            f"📖 <b>{subject}</b>\n\n"
            f"<i>Просто отправьте текст ДЗ в ответ на это сообщение или следующим сообщением.</i>",
            parse_mode="HTML"
        )
        
        await callback.answer("✏️ Напишите ДЗ в чате")
        
    except Exception as e:
        logger.error(f"Ошибка при начале быстрого добавления ДЗ: {e}", exc_info=True)
        await callback.answer("❌ Ошибка. Попробуйте позже.", show_alert=True)


@router.message(F.text & ~F.text.startswith("/"))
async def handle_quick_hw_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if user_id not in quick_hw_pending:
        return  
    
    pending_data = quick_hw_pending[user_id]
    
    if message.chat.id != pending_data.get("chat_id"):
        return
    
    try:
        timestamp = datetime.fromisoformat(pending_data["timestamp"])
        moscow_tz = tz.gettz("Europe/Moscow")
        now = datetime.now(moscow_tz)
        if (now - timestamp).total_seconds() > 300: 
            del quick_hw_pending[user_id]
            return
    except:
        pass
    
    task = message.text.strip()
    if not task:
        return
    
    subject = pending_data["subject"]
    lesson_id = pending_data["lesson_id"]
    
    del quick_hw_pending[user_id]
    
    await state.set_state(QuickHomeworkStates.selecting_date)
    await state.update_data(
        lesson_id=lesson_id,
        subject=subject,
        task=task,
        quick_mode=True,
        group_chat_id=message.chat.id
    )
    
    calendar_kb = quick_homework_calendar.create_calendar()
    
    await message.reply(
        f"📝 <b>Добавление ДЗ</b>\n\n"
        f"📖 Предмет: <b>{subject}</b>\n"
        f"✏️ Задание: {task}\n\n"
        f"📅 Выберите дату, к которой нужно выполнить ДЗ:",
        reply_markup=calendar_kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("qhw_cal:"), QuickHomeworkStates.selecting_date)
async def quick_hw_calendar_callback(callback: CallbackQuery, state: FSMContext):
    action, selected_date, year, month = quick_homework_calendar.parse_callback(callback.data)
    
    if action == "ignore":
        await callback.answer()
        return
    
    if action == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Добавление ДЗ отменено.")
        await callback.answer()
        return
    
    if action in ["prev_month", "next_month", "prev_year", "next_year"]:
        calendar_kb = quick_homework_calendar.create_calendar(year=year, month=month)
        data = await state.get_data()
        
        await callback.message.edit_text(
            f"📝 <b>Добавление ДЗ</b>\n\n"
            f"📖 Предмет: <b>{data.get('subject', '')}</b>\n"
            f"✏️ Задание: {data.get('task', '')}\n\n"
            f"📅 Выберите дату, к которой нужно выполнить ДЗ:",
            reply_markup=calendar_kb,
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    if action in ["select", "today"]:
        await state.update_data(target_date=selected_date.isoformat())
        await state.set_state(QuickHomeworkStates.confirming)
        
        data = await state.get_data()
        date_str = format_date_ru(selected_date)
        
        confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="qhw_confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="qhw_cancel")
            ]
        ])
        
        await callback.message.edit_text(
            f"📝 <b>Проверьте данные ДЗ:</b>\n\n"
            f"📅 <b>{date_str}</b>\n"
            f"📖 {data.get('subject', '')}\n"
            f"✏️ {data.get('task', '')}\n\n"
            f"Всё верно?",
            reply_markup=confirm_kb,
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data == "qhw_confirm", QuickHomeworkStates.confirming)
async def quick_hw_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    target_date = date.fromisoformat(data.get("target_date"))
    subject = data.get("subject", "")
    task = data.get("task", "")
    
    success = homework_storage.add_homework(target_date, subject, task)
    
    await state.clear()
    
    if success:
        date_str = format_date_ru(target_date)
        user_name = callback.from_user.first_name or "Участник"
        
        await callback.message.edit_text(
            f"✅ <b>ДЗ добавлено!</b>\n\n"
            f"👤 Добавил: {user_name}\n"
            f"📅 <b>{date_str}</b>\n"
            f"📖 {subject}\n"
            f"✏️ {task}",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка при сохранении ДЗ. Попробуйте позже."
        )
    
    await callback.answer()


@router.callback_query(F.data == "qhw_cancel", QuickHomeworkStates.confirming)
async def quick_hw_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Добавление ДЗ отменено.")
    await callback.answer()


@router.callback_query(F.data == "qhw_cancel")
async def quick_hw_cancel_general(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Добавление ДЗ отменено.")
    await callback.answer()


def is_headman_or_proforg(user_id: int) -> bool:
    user_data = group_manager.get_member(user_id)
    if not user_data:
        return False
    return user_data.get("role") in ["Староста", "Профорг", "Зам старосты"]
