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


class FileManagerStates(StatesGroup):
    waiting_for_lesson_name = State()
    waiting_for_files = State()


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
    
    await callback.message.answer(
        "📝 Введите название пары, для которой хотите добавить файлы:\n\n"
        "Например: <b>Математический анализ</b> или <b>Информатика</b>",
        parse_mode="HTML"
    )
    
    await state.set_state(FileManagerStates.waiting_for_lesson_name)


@router.message(FileManagerStates.waiting_for_lesson_name)
async def process_lesson_name(message: Message, state: FSMContext):
    lesson_name = message.text.strip()
    
    await state.update_data(lesson_name=lesson_name)
    
    await message.answer(
        f"📚 Пара: <b>{lesson_name}</b>\n\n"
        f"Теперь отправьте файлы, которые нужно прикреплять к уведомлениям об этой паре.\n\n"
        f"Вы можете отправить несколько файлов. Когда закончите, отправьте команду /done",
        parse_mode="HTML"
    )
    
    await state.set_state(FileManagerStates.waiting_for_files)


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
            f"✅ Файл <b>{file_name}</b> добавлен!\n\n"
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
            callback_data=f"delete_files:{lesson_name}"
        )])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.answer(
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("delete_files:"))
async def handle_delete_files(callback: CallbackQuery):
    lesson_name = callback.data.split(":", 1)[1]
    
    storage.remove_lesson_files(lesson_name)
    
    await callback.answer("✅ Файлы удалены!", show_alert=True)
    await callback.message.edit_text(
        f"✅ Файлы для пары <b>{lesson_name}</b> успешно удалены.",
        parse_mode="HTML"
    )
