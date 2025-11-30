import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime

from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from commands.group.group_manager import group_manager

logger = logging.getLogger(__name__)
router = Router()


class HeadmanReasonStates(StatesGroup):
    waiting_for_reason = State()


class HeadmanChecker:
    
    def __init__(self, bot: Bot, group_chat_id: str):
        self.bot = bot
        self.group_chat_id = group_chat_id
        self.pending_checks: Dict[str, Dict] = {}  # lesson_id -> check_data
        self.timeout_minutes = 20
        logger.info(f"HeadmanChecker инициализирован с group_chat_id: {group_chat_id}")
    
    async def ask_headman_presence(self, lesson_id: str, lesson_name: str, lesson_time: str):
        logger.info(f"=== ЗАПРОС СТАРОСТЕ ===")
        logger.info(f"Пара: {lesson_name}, время: {lesson_time}, lesson_id: {lesson_id}")
        
        headman = group_manager.get_headman()
        
        if not headman:
            logger.warning("Староста не найден в системе. Проверьте, что староста зарегистрирован с ролью 'Староста'")
            return
        
        logger.info(f"Найден староста: {headman.get('full_name')} (ID: {headman.get('user_id')})")
        
        headman_id = headman.get("user_id")
        if not headman_id:
            logger.warning("У старосты не найден user_id")
            return
        
        self.pending_checks[lesson_id] = {
            "headman_id": headman_id,
            "lesson_name": lesson_name,
            "lesson_time": lesson_time,
            "asked_at": datetime.now(),
            "responded": False,
            "message_id": None
        }
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, буду",
                    callback_data=f"headman_present:{lesson_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Нет",
                    callback_data=f"headman_absent:{lesson_id}"
                )
            ]
        ])
        
        message_text = (
            f"📚 <b>Пара: {lesson_name}</b>\n"
            f"🕐 Время: {lesson_time}\n\n"
            f"❓ <b>Будете ли вы на паре?</b>\n\n"
            f"<i>Если не ответите в течение {self.timeout_minutes} минут, "
            f"группа будет предупреждена, что вы не сможете отметить студентов.</i>"
        )
        
        try:
            logger.info(f"Отправляем сообщение старосте (chat_id: {headman_id})...")
            sent_message = await self.bot.send_message(
                chat_id=headman_id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            self.pending_checks[lesson_id]["message_id"] = sent_message.message_id
            logger.info(f"✅ Сообщение отправлено старосте! message_id: {sent_message.message_id}")
            
            asyncio.create_task(self._check_timeout(lesson_id))
            logger.info(f"Запущен таймер на {self.timeout_minutes} минут")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке сообщения старосте: {e}", exc_info=True)
    
    async def _check_timeout(self, lesson_id: str):
        await asyncio.sleep(self.timeout_minutes * 60)
        
        if lesson_id in self.pending_checks:
            check_data = self.pending_checks[lesson_id]
            
            if not check_data.get("responded"):
                logger.info(f"Староста не ответил на запрос о паре '{check_data['lesson_name']}'")
                await self._notify_group_no_headman(
                    lesson_name=check_data["lesson_name"],
                    lesson_time=check_data["lesson_time"],
                    reason=None  
                )
                
                try:
                    await self.bot.edit_message_text(
                        chat_id=check_data["headman_id"],
                        message_id=check_data["message_id"],
                        text=(
                            f"📚 <b>Пара: {check_data['lesson_name']}</b>\n"
                            f"🕐 Время: {check_data['lesson_time']}\n\n"
                            f"⏰ <b>Время на ответ истекло.</b>\n"
                            f"Группа была предупреждена."
                        ),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Ошибка при редактировании сообщения: {e}")
                
                del self.pending_checks[lesson_id]
    
    async def handle_headman_present(self, lesson_id: str):
        if lesson_id in self.pending_checks:
            check_data = self.pending_checks[lesson_id]
            check_data["responded"] = True
            
            try:
                await self.bot.edit_message_text(
                    chat_id=check_data["headman_id"],
                    message_id=check_data["message_id"],
                    text=(
                        f"📚 <b>Пара: {check_data['lesson_name']}</b>\n"
                        f"🕐 Время: {check_data['lesson_time']}\n\n"
                        f"✅ <b>Отлично! Вы будете на паре.</b>"
                    ),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Ошибка при редактировании сообщения: {e}")
            
            logger.info(f"Староста подтвердил присутствие на паре '{check_data['lesson_name']}'")
            del self.pending_checks[lesson_id]
    
    async def handle_headman_absent(self, lesson_id: str) -> Dict:
        if lesson_id in self.pending_checks:
            check_data = self.pending_checks[lesson_id]
            check_data["responded"] = True
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🚫 Без причины",
                    callback_data=f"headman_no_reason:{lesson_id}"
                )]
            ])
            
            try:
                await self.bot.edit_message_text(
                    chat_id=check_data["headman_id"],
                    message_id=check_data["message_id"],
                    text=(
                        f"📚 <b>Пара: {check_data['lesson_name']}</b>\n"
                        f"🕐 Время: {check_data['lesson_time']}\n\n"
                        f"📝 <b>Пожалуйста, напишите причину отсутствия:</b>\n\n"
                        f"<i>Или нажмите кнопку ниже, чтобы отправить без причины.</i>"
                    ),
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Ошибка при редактировании сообщения: {e}")
            
            return check_data
        return {}
    
    async def handle_reason_provided(self, lesson_id: str, reason: Optional[str] = None):
        if lesson_id in self.pending_checks:
            check_data = self.pending_checks[lesson_id]
            
            await self._notify_group_no_headman(
                lesson_name=check_data["lesson_name"],
                lesson_time=check_data["lesson_time"],
                reason=reason
            )
            
            reason_text = f"Причина: {reason}" if reason else "Без указания причины"
            try:
                await self.bot.edit_message_text(
                    chat_id=check_data["headman_id"],
                    message_id=check_data["message_id"],
                    text=(
                        f"📚 <b>Пара: {check_data['lesson_name']}</b>\n"
                        f"🕐 Время: {check_data['lesson_time']}\n\n"
                        f"✅ <b>Группа предупреждена о вашем отсутствии.</b>\n"
                        f"<i>{reason_text}</i>"
                    ),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Ошибка при редактировании сообщения: {e}")
            
            logger.info(f"Староста отсутствует на паре '{check_data['lesson_name']}'. Причина: {reason or 'не указана'}")
            del self.pending_checks[lesson_id]
    
    async def _notify_group_no_headman(self, lesson_name: str, lesson_time: str, reason: Optional[str]):
        headman = group_manager.get_headman()
        headman_name = headman.get("full_name", "Староста") if headman else "Староста"
        
        if reason:
            message_text = (
                f"⚠️ <b>Внимание!</b>\n\n"
                f"📚 Пара: <b>{lesson_name}</b>\n"
                f"🕐 Время: {lesson_time}\n\n"
                f"👔 {headman_name} не сможет присутствовать на паре "
                f"и отметить студентов.\n\n"
                f"📝 <b>Причина:</b> {reason}"
            )
        else:
            message_text = (
                f"⚠️ <b>Внимание!</b>\n\n"
                f"📚 Пара: <b>{lesson_name}</b>\n"
                f"🕐 Время: {lesson_time}\n\n"
                f"👔 {headman_name} не сможет присутствовать на паре "
                f"и отметить студентов."
            )
        
        try:
            await self.bot.send_message(
                chat_id=self.group_chat_id,
                text=message_text,
                parse_mode="HTML"
            )
            logger.info(f"Группа предупреждена об отсутствии старосты на паре '{lesson_name}'")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления в группу: {e}")
    
    def get_pending_check(self, lesson_id: str) -> Optional[Dict]:
        return self.pending_checks.get(lesson_id)


headman_checker: Optional[HeadmanChecker] = None


def set_headman_checker(checker: HeadmanChecker):
    global headman_checker
    headman_checker = checker


def get_headman_checker() -> Optional[HeadmanChecker]:
    return headman_checker


@router.callback_query(F.data.startswith("headman_present:"))
async def handle_present_callback(callback: CallbackQuery):
    lesson_id = callback.data.split(":")[1]
    
    checker = get_headman_checker()
    if checker:
        await checker.handle_headman_present(lesson_id)
    
    await callback.answer("Отлично! Хорошей пары! 📚")


@router.callback_query(F.data.startswith("headman_absent:"))
async def handle_absent_callback(callback: CallbackQuery, state: FSMContext):
    lesson_id = callback.data.split(":")[1]
    
    checker = get_headman_checker()
    if checker:
        check_data = await checker.handle_headman_absent(lesson_id)
        if check_data:
            await state.update_data(pending_lesson_id=lesson_id)
            await state.set_state(HeadmanReasonStates.waiting_for_reason)
    
    await callback.answer()


@router.callback_query(F.data.startswith("headman_no_reason:"))
async def handle_no_reason_callback(callback: CallbackQuery, state: FSMContext):
    lesson_id = callback.data.split(":")[1]
    
    checker = get_headman_checker()
    if checker:
        await checker.handle_reason_provided(lesson_id, reason=None)
    
    await state.clear()
    await callback.answer("Группа предупреждена")


@router.message(HeadmanReasonStates.waiting_for_reason)
async def handle_reason_message(message: Message, state: FSMContext):
    data = await state.get_data()
    lesson_id = data.get("pending_lesson_id")
    
    if lesson_id:
        checker = get_headman_checker()
        if checker:
            await checker.handle_reason_provided(lesson_id, reason=message.text)
    
    await state.clear()
