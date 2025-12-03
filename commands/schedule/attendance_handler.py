import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from commands.group.group_manager import group_manager
from commands.schedule.schedule_storage import ScheduleStorage

router = Router()
logger = logging.getLogger(__name__)

storage = ScheduleStorage()


@router.callback_query(F.data.startswith("att:"))
async def handle_attendance_request(callback: CallbackQuery):
    try:
        lesson_id = callback.data.split(":", 1)[1]
        
        user_id = callback.from_user.id
        username = callback.from_user.username
        first_name = callback.from_user.first_name
        last_name = callback.from_user.last_name or ""
        
        user_data = group_manager.get_member(user_id)
        if user_data:
            full_name = user_data.get("full_name", f"{first_name} {last_name}".strip())
        else:
            full_name = f"{first_name} {last_name}".strip()
        
        request_data = {
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "timestamp": callback.message.date.isoformat()
        }
        
        was_added = storage.add_attendance_request(lesson_id, request_data)
        
        if was_added:
            await _notify_headman(callback, lesson_id, full_name)
            
            await callback.answer(
                "✅ Ваш запрос на отметку отправлен старосте!",
                show_alert=True
            )
        else:
            await callback.answer(
                "ℹ️ Вы уже отправили запрос на отметку для этой пары.",
                show_alert=False
            )
        
        await _update_attendance_counter(callback, lesson_id)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса на отметку: {e}", exc_info=True)
        await callback.answer(
            "❌ Произошла ошибка. Попробуйте позже.",
            show_alert=True
        )


async def _notify_headman(callback: CallbackQuery, lesson_id: str, student_name: str):
    try:
        headman = group_manager.get_headman()
        
        if not headman:
            logger.warning("Староста не найден в группе")
            return
        
        headman_id = headman.get("user_id")
        
        attendance_list = storage.get_attendance_list(lesson_id)
        
        message_text = f"📝 <b>Новый запрос на отметку</b>\n\n"
        message_text += f"👤 <b>{student_name}</b> попросил отметить его на паре.\n\n"
        message_text += f"Всего запросов: <b>{len(attendance_list)}</b>\n\n"
        message_text += "Список всех запросов:\n"
        
        for i, req in enumerate(attendance_list, 1):
            username_str = f"@{req['username']}" if req.get('username') else "без username"
            message_text += f"{i}. {req['full_name']} ({username_str})\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📋 Полный список отметок",
                callback_data=f"view_attendance:{lesson_id}"
            )]
        ])
        
        await callback.bot.send_message(
            chat_id=headman_id,
            text=message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления старосте: {e}", exc_info=True)


async def _update_attendance_counter(callback: CallbackQuery, lesson_id: str):
    try:
        attendance_list = storage.get_attendance_list(lesson_id)
        count = len(attendance_list)
        
        buttons = [
            [InlineKeyboardButton(
                text=f"✋ Меня надо отметить на паре ({count})" if count > 0 else "✋ Меня надо отметить на паре",
                callback_data=f"att:{lesson_id}"
            )],
            [InlineKeyboardButton(
                text="📝 Добавить ДЗ",
                callback_data=f"quick_hw:{lesson_id}"
            )]
        ]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        logger.info(f"Обновлена клавиатура для lesson_id={lesson_id}, счетчик={count}")
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении счетчика: {e}", exc_info=True)


@router.callback_query(F.data.startswith("view_attendance:"))
async def handle_view_attendance(callback: CallbackQuery):
    try:
        user_id = callback.from_user.id
        user_data = group_manager.get_member(user_id)
        
        if not user_data or user_data.get("role") != "Староста":
            await callback.answer(
                "⛔ Эта функция доступна только старосте.",
                show_alert=True
            )
            return
        
        lesson_id = callback.data.split(":", 1)[1]
        
        attendance_list = storage.get_attendance_list(lesson_id)
        
        if not attendance_list:
            await callback.answer(
                "ℹ️ Пока нет запросов на отметку.",
                show_alert=True
            )
            return
        
        message_text = f"📋 <b>Список студентов для отметки</b>\n\n"
        message_text += f"Всего: <b>{len(attendance_list)}</b> человек\n\n"
        
        for i, req in enumerate(attendance_list, 1):
            username_str = f"@{req['username']}" if req.get('username') else "без username"
            message_text += f"{i}. <b>{req['full_name']}</b>\n"
            message_text += f"   {username_str}\n\n"
        
        await callback.answer()
        await callback.message.answer(message_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка при просмотре списка отметок: {e}", exc_info=True)
        await callback.answer(
            "❌ Произошла ошибка. Попробуйте позже.",
            show_alert=True
        )
