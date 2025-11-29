import logging
import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from commands.group.group_manager import group_manager
from commands.schedule.schedule_storage import ScheduleStorage

router = Router()
logger = logging.getLogger(__name__)

storage = ScheduleStorage()

ALL_SUBJECTS = [
    "ЛК Информатика",
    "ЛК Физика",
    "ПР Физическая культура и спорт",
    "ПР Иностранный язык",
    "ЛК История России",
    "ЛК Линейная алгебра и аналитическая геометрия",
    "ПР Математический анализ",
    "ПР История России",
    "ПР Линейная алгебра и аналитическая геометрия",
    "ПР Информатика",
    "ПР Физика",
    "ПР Математическая логика и теория алгоритмов",
    "ЛК Математический анализ",
    "ЛК Математическая логика и теория алгоритмов",
    "ЛК Введение в профессиональную деятельность",
    "ЛАБ Физика (1 п/г)",
    "ЛАБ Физика (2 п/г)",
]


class FileManagerStates(StatesGroup):
    waiting_for_lesson_name = State()
    waiting_for_files = State()
    selecting_subject_page = State() 


def create_subjects_keyboard(page: int = 0, items_per_page: int = 8) -> InlineKeyboardMarkup:
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_subjects = ALL_SUBJECTS[start_idx:end_idx]
    
    buttons = []
    for subject in current_subjects:
        subject_idx = ALL_SUBJECTS.index(subject)
        buttons.append([InlineKeyboardButton(
            text=subject,
            callback_data=f"sel_subj:{subject_idx}"
        )])
    
    nav_buttons = []
    total_pages = (len(ALL_SUBJECTS) + items_per_page - 1) // items_per_page
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"subj_page:{page - 1}"
        ))
    
    nav_buttons.append(InlineKeyboardButton(
        text=f"{page + 1}/{total_pages}",
        callback_data="subj_page_info"
    ))
    
    if end_idx < len(ALL_SUBJECTS):
        nav_buttons.append(InlineKeyboardButton(
            text="Вперед ➡️",
            callback_data=f"subj_page:{page + 1}"
        ))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="cancel_file_upload"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("manage_files"))
async def cmd_manage_files(message: Message):
    user_id = message.from_user.id
    user_data = group_manager.get_member(user_id)
    
    if not user_data or user_data.get("role") not in ["Староста", "Профорг", "Зам старосты"]:
        await message.answer(
            "⛔ Эта команда доступна только старосте и профоргу."
        )
        return
    
    all_files = storage.get_all_lesson_files()
    
    if not all_files:
        message_text = "📂 <b>Управление файлами для пар</b>\n\n"
        message_text += "Пока не добавлено ни одного файла.\n\n"
        message_text += "Используйте кнопки ниже для управления:"
    else:
        message_text = "📂 <b>Управление файлами для пар</b>\n\n"
        message_text += "Текущие файлы:\n\n"
        
        for lesson_name, files in all_files.items():
            message_text += f"📚 <b>{lesson_name}</b>\n"
            for file_path in files:
                file_name = os.path.basename(file_path)
                message_text += f"   📎 {file_name}\n"
            message_text += "\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="➕ Добавить файлы для пары",
            callback_data="add_lesson_files"
        )],
        [InlineKeyboardButton(
            text="🗑 Удалить файлы пары",
            callback_data="remove_lesson_files"
        )]
    ])
    
    await message.answer(message_text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "add_lesson_files")
async def handle_add_files(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    await state.set_state(FileManagerStates.selecting_subject_page)
    await state.update_data(current_page=0)
    
    keyboard = create_subjects_keyboard(page=0)
    
    await callback.message.answer(
        "📚 <b>Выберите предмет для добавления файлов:</b>\n\n"
        "Нажмите на кнопку с нужным предметом:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("subj_page:"))
async def handle_subject_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    await state.update_data(current_page=page)
    
    keyboard = create_subjects_keyboard(page=page)
    
    await callback.message.edit_text(
        "📚 <b>Выберите предмет для добавления файлов:</b>\n\n"
        "Нажмите на кнопку с нужным предметом:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "subj_page_info")
async def handle_page_info(callback: CallbackQuery):
    await callback.answer("Текущая страница", show_alert=False)


@router.callback_query(F.data.startswith("sel_subj:"))
async def handle_select_subject(callback: CallbackQuery, state: FSMContext):
    subject_idx = int(callback.data.split(":")[1])
    
    if 0 <= subject_idx < len(ALL_SUBJECTS):
        lesson_name = ALL_SUBJECTS[subject_idx]
        await state.update_data(lesson_name=lesson_name)
        
        await callback.message.edit_text(
            f"✅ <b>Выбран предмет:</b> {lesson_name}\n\n"
            f"📎 Теперь отправьте файлы, которые нужно прикреплять к уведомлениям об этой паре.\n\n"
            f"Вы можете отправить несколько файлов. Когда закончите, отправьте команду /done",
            parse_mode="HTML"
        )
        
        await state.set_state(FileManagerStates.waiting_for_files)
        await callback.answer()
    else:
        await callback.answer("❌ Ошибка: предмет не найден", show_alert=True)


@router.callback_query(F.data == "cancel_file_upload")
async def handle_cancel_upload(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Добавление файлов отменено.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(FileManagerStates.waiting_for_files, F.document)
async def process_file(message: Message, state: FSMContext):
    try:
        document = message.document
        file_id = document.file_id
        file_name = document.file_name
        
        file = await message.bot.get_file(file_id)
        
        files_dir = "data/lesson_files"
        os.makedirs(files_dir, exist_ok=True)
        
        file_path = os.path.join(files_dir, file_name)
        await message.bot.download_file(file.file_path, file_path)
        
        data = await state.get_data()
        lesson_name = data["lesson_name"]
        
        storage.add_lesson_files(lesson_name, [file_path])
        
        await message.answer(
            f"✅ Файл <b>{file_name}</b> добавлен для <b>{lesson_name}</b>!\n\n"
            f"Отправьте еще файлы или /done для завершения.",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке файла: {e}", exc_info=True)
        await message.answer("❌ Ошибка при сохранении файла. Попробуйте еще раз.")


@router.message(FileManagerStates.waiting_for_files, Command("done"))
async def finish_adding_files(message: Message, state: FSMContext):
    data = await state.get_data()
    lesson_name = data["lesson_name"]
    
    await state.clear()
    
    await message.answer(
        f"✅ Файлы для пары <b>{lesson_name}</b> успешно добавлены!\n\n"
        f"Теперь они будут автоматически отправляться за 10 минут до начала пары.",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "remove_lesson_files")
async def handle_remove_files(callback: CallbackQuery):
    await callback.answer()
    
    all_files = storage.get_all_lesson_files()
    
    if not all_files:
        await callback.message.answer("ℹ️ Нет файлов для удаления.")
        return
    
    buttons = []
    for lesson_name in all_files.keys():
        buttons.append([InlineKeyboardButton(
            text=f"🗑 {lesson_name}",
            callback_data=f"delete_files:{lesson_name[:50]}"  # Ограничение длины callback_data
        )])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.answer(
        "🗑 <b>Выберите предмет для удаления файлов:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("delete_files:"))
async def handle_delete_files(callback: CallbackQuery):
    lesson_name_partial = callback.data.split(":", 1)[1]
    
    all_files = storage.get_all_lesson_files()
    lesson_name = None
    for name in all_files.keys():
        if name.startswith(lesson_name_partial) or name == lesson_name_partial:
            lesson_name = name
            break
    
    if lesson_name:
        storage.remove_lesson_files(lesson_name)
        await callback.answer("✅ Файлы удалены!", show_alert=True)
        await callback.message.edit_text(
            f"✅ Файлы для пары <b>{lesson_name}</b> успешно удалены.",
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Предмет не найден", show_alert=True)
