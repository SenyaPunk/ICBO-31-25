import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from dateutil import tz

from aiogram import Bot, Router, F
from aiogram.types import (
    Message, 
    CallbackQuery, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from commands.group.group_manager import group_manager, Role
from commands.homework.homework_storage import HomeworkStorage, get_academic_week_number
from commands.notifications.notifications import get_user_notifications

router = Router()
logger = logging.getLogger(__name__)

WEEKDAYS_RU = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]


class DigestEditStates(StatesGroup):
    editing_hw = State()
    adding_hw_subject = State()
    adding_hw_task = State()
    adding_hw_date = State()
    editing_km = State()
    adding_km_subject = State()
    adding_km_desc = State()
    adding_km_date = State()


class WeeklyDigestNotifier:
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.storage = HomeworkStorage()
        self.moscow_tz = tz.gettz("Europe/Moscow")
        self.is_running = False
        self.check_interval = 60  
        self.digest_hour = 20  
        self.digest_minute = 0
        self.digest_weekday = 6 
        
        self.cleanup_hour = 0
        self.cleanup_minute = 0
        self.last_cleanup_date: Optional[str] = None
        
        self.pending_digests: Dict[int, Dict] = {}
    
    async def start(self):
        self.is_running = True
        logger.info("Система еженедельных дайджестов запущена")
        
        while self.is_running:
            try:
                await self._check_and_send_digest()
                await self._check_and_cleanup_old_weeks()
            except Exception as e:
                logger.error(f"Ошибка в системе дайджестов: {e}", exc_info=True)
            
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        self.is_running = False
        logger.info("Система еженедельных дайджестов остановлена")
    
    async def _check_and_cleanup_old_weeks(self):
        now = datetime.now(self.moscow_tz)
        today_str = now.strftime("%Y-%m-%d")
        
        if (now.hour == self.cleanup_hour and 
            now.minute == self.cleanup_minute and
            self.last_cleanup_date != today_str):
            
            logger.info("Запуск ежедневной очистки старых недель...")
            result = self.storage.cleanup_old_weeks()
            self.last_cleanup_date = today_str
            
            if result["removed_homework_weeks"] or result["removed_control_weeks"]:
                logger.info(
                    f"🧹 Очищены прошедшие недели. "
                    f"Текущая: {result['current_week']}. "
                    f"ДЗ: {result['removed_homework_weeks']}, "
                    f"КМ: {result['removed_control_weeks']}"
                )
            else:
                logger.info(f"🧹 Очистка не требуется. Текущая неделя: {result['current_week']}")
    
    async def _check_and_send_digest(self):
        now = datetime.now(self.moscow_tz)
        
        if (now.weekday() == self.digest_weekday and 
            now.hour == self.digest_hour and 
            now.minute == self.digest_minute):
            
            today_str = now.strftime("%Y-%m-%d")
            if self.storage.data.get("last_digest_date") == today_str:
                return
            
            logger.info("Время отправки еженедельного дайджеста!")
            await self._send_digest_to_headman()
            
            self.storage.data["last_digest_date"] = today_str
            self.storage._save_data()
    
    def get_next_week_dates(self) -> Tuple[date, date]:
        today = datetime.now(self.moscow_tz).date()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        next_sunday = next_monday + timedelta(days=6)
        return next_monday, next_sunday
    
    def get_week_number(self, target_date: Optional[date] = None) -> int:
        if target_date is None:
            next_monday, _ = self.get_next_week_dates()
            target_date = next_monday
        return get_academic_week_number(target_date)
    
    def get_current_week_number(self) -> int:
        today = datetime.now(self.moscow_tz).date()
        return get_academic_week_number(today)
    
    def format_homework_digest(self) -> str:
        self.storage.reload_data()
        
        next_monday, next_sunday = self.get_next_week_dates()
        week_num = self.get_week_number()
        
        upcoming_hw = self.storage.get_all_upcoming_homework()
        
        week_hw = []
        for hw_date, subject, tasks in upcoming_hw:
            if next_monday <= hw_date <= next_sunday:
                week_hw.append((hw_date, subject, tasks))
        
        if not week_hw:
            return f"ДЗ | {week_num} НЕДЕЛЯ\n\n🎉 На следующую неделю заданий нет!"
        
        hw_by_date: Dict[date, List[Tuple[str, List[str]]]] = {}
        for hw_date, subject, tasks in week_hw:
            if hw_date not in hw_by_date:
                hw_by_date[hw_date] = []
            hw_by_date[hw_date].append((subject, tasks))
        
        text = f"📝 ДЗ | {week_num} НЕДЕЛЯ\n\n"
        
        for hw_date in sorted(hw_by_date.keys()):
            weekday = WEEKDAYS_RU[hw_date.weekday()]
            date_str = hw_date.strftime("%d.%m.%Y")
            text += f"📅 <b>{weekday} ({date_str})</b>:\n"
            
            for subject, tasks in hw_by_date[hw_date]:
                clean_subject = subject
                for prefix in ["ЛК ", "ПР ", "ЛАБ "]:
                    if subject.startswith(prefix):
                        clean_subject = subject[len(prefix):]
                        break
                
                for task in tasks:
                    text += f"   • {clean_subject}: {task}\n"
            text += "\n"
        
        return text
    
    def format_control_measures_digest(self) -> str:
        self.storage.reload_data()
        
        today = datetime.now(self.moscow_tz).date()
        next_monday, next_sunday = self.get_next_week_dates()
        
        upcoming_km = self.storage.get_all_upcoming_control_measures()
        
        current_week_num = self.get_current_week_number()
        next_week_num = self.get_week_number()
        
        current_week_km = []
        next_week_km = []
        
        for km_date, subject, descriptions in upcoming_km:
            km_week = get_academic_week_number(km_date)
            if km_week == current_week_num:
                current_week_km.append((km_date, subject, descriptions))
            elif km_week == next_week_num:
                next_week_km.append((km_date, subject, descriptions))
        
        if not current_week_km and not next_week_km:
            return "📋 ТЕКУЩИЕ КОНТРОЛЬНЫЕ МЕРОПРИЯТИЯ\n\n🎉 Контрольных мероприятий нет!"
        
        text = "📋 <b>ТЕКУЩИЕ КОНТРОЛЬНЫЕ МЕРОПРИЯТИЯ</b>\n\n"
        
        if current_week_km:
            text += f"<b>{current_week_num} неделя:</b>\n"
            for km_date, subject, descriptions in sorted(current_week_km, key=lambda x: x[0]):
                weekday = WEEKDAYS_RU[km_date.weekday()]
                date_str = km_date.strftime("%d.%m")
                
                clean_subject = subject
                for prefix in ["ЛК ", "ПР ", "ЛАБ "]:
                    if subject.startswith(prefix):
                        clean_subject = subject[len(prefix):]
                        break
                
                for desc in descriptions:
                    text += f"📌 {date_str} / {weekday} / {clean_subject} {desc}\n"
            text += "\n"
        
        if next_week_km:
            text += f"<b>{next_week_num} неделя:</b>\n"
            for km_date, subject, descriptions in sorted(next_week_km, key=lambda x: x[0]):
                weekday = WEEKDAYS_RU[km_date.weekday()]
                date_str = km_date.strftime("%d.%m")
                
                clean_subject = subject
                for prefix in ["ЛК ", "ПР ", "ЛАБ "]:
                    if subject.startswith(prefix):
                        clean_subject = subject[len(prefix):]
                        break
                
                for desc in descriptions:
                    text += f"📌 {date_str} / {weekday} / {clean_subject} {desc}\n"
        
        return text
    
    async def _send_digest_to_headman(self):
        headman = group_manager.get_headman()
        if not headman:
            logger.warning("Староста не найден, дайджест не отправлен")
            return
        
        headman_id = headman["user_id"]
        
        hw_text = self.format_homework_digest()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="digest_send_hw"),
                InlineKeyboardButton(text="✏️ Редактировать", callback_data="digest_edit_hw")
            ],
            [
                InlineKeyboardButton(text="⏭️ Пропустить ДЗ", callback_data="digest_skip_hw")
            ]
        ])
        
        try:
            await self.bot.send_message(
                chat_id=headman_id,
                text=f"📢 <b>Еженедельный дайджест ДЗ</b>\n\n{hw_text}\n\n"
                     f"Проверьте и выберите действие:",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            self.pending_digests[headman_id] = {
                "hw_text": hw_text,
                "km_text": self.format_control_measures_digest(),
                "hw_sent": False,
                "km_sent": False
            }
            
            logger.info(f"Дайджест ДЗ отправлен старосте {headman_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки дайджеста старосте: {e}", exc_info=True)
    
    async def send_digest_to_subscribers(self, digest_type: str, text: str) -> Tuple[int, int]:
        
        all_members = group_manager.get_all_members()
        
        success_count = 0
        failed_count = 0
        
        for member_id, member_data in all_members.items():
            notifications = member_data.get('notifications', {})
            if notifications.get(digest_type, False):
                try:
                    category_title = "📚 Домашние задания" if digest_type == "homework" else "📋 Контрольные мероприятия"
                    
                    await self.bot.send_message(
                        chat_id=int(member_id),
                        text=f"📢 <b>Еженедельная рассылка: {category_title}</b>\n"
                             f"{'─' * 30}\n\n{text}",
                        parse_mode="HTML"
                    )
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Ошибка отправки дайджеста пользователю {member_id}: {e}")
        
        return success_count, failed_count


weekly_digest_notifier: Optional[WeeklyDigestNotifier] = None


def set_weekly_digest_notifier(notifier: WeeklyDigestNotifier):
    global weekly_digest_notifier
    weekly_digest_notifier = notifier


def get_weekly_digest_notifier() -> Optional[WeeklyDigestNotifier]:
    return weekly_digest_notifier





@router.callback_query(F.data == "digest_send_hw")
async def handle_send_hw_digest(callback: CallbackQuery):
    notifier = get_weekly_digest_notifier()
    if not notifier:
        await callback.answer("Ошибка: система не инициализирована", show_alert=True)
        return
    
    user_id = callback.from_user.id
    if user_id not in notifier.pending_digests:
        await callback.answer("Дайджест устарел", show_alert=True)
        return
    
    hw_text = notifier.pending_digests[user_id]["hw_text"]
    
    await callback.message.edit_text(
        f"{hw_text}\n\n⏳ <b>Отправка подписчикам...</b>",
        parse_mode="HTML"
    )
    
    success, failed = await notifier.send_digest_to_subscribers("homework", hw_text)
    
    notifier.pending_digests[user_id]["hw_sent"] = True
    
    await callback.message.edit_text(
        f"{hw_text}\n\n"
        f"✅ <b>Дайджест ДЗ отправлен!</b>\n"
        f"Доставлено: {success} | Ошибок: {failed}",
        parse_mode="HTML"
    )
    
    await _send_km_digest(callback, notifier, user_id)
    await callback.answer()


@router.callback_query(F.data == "digest_skip_hw")
async def handle_skip_hw_digest(callback: CallbackQuery):
    notifier = get_weekly_digest_notifier()
    if not notifier:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    user_id = callback.from_user.id
    if user_id not in notifier.pending_digests:
        await callback.answer("Дайджест устарел", show_alert=True)
        return
    
    await callback.message.edit_text("⏭️ Рассылка ДЗ пропущена.")
    
    await _send_km_digest(callback, notifier, user_id)
    await callback.answer()


@router.callback_query(F.data == "digest_edit_hw")
async def handle_edit_hw_digest(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить ДЗ", callback_data="digest_add_hw")],
        [InlineKeyboardButton(text="➖ Удалить ДЗ", callback_data="digest_del_hw")],
        [InlineKeyboardButton(text="🔄 Обновить текст", callback_data="digest_refresh_hw")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="digest_back_hw")]
    ])
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "digest_refresh_hw")
async def handle_refresh_hw(callback: CallbackQuery):
    notifier = get_weekly_digest_notifier()
    if not notifier:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    user_id = callback.from_user.id
    hw_text = notifier.format_homework_digest()
    
    if user_id in notifier.pending_digests:
        notifier.pending_digests[user_id]["hw_text"] = hw_text
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="digest_send_hw"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="digest_edit_hw")
        ],
        [
            InlineKeyboardButton(text="⏭️ Пропустить ДЗ", callback_data="digest_skip_hw")
        ]
    ])
    
    await callback.message.edit_text(
        f"📢 <b>Еженедельный дайджест ДЗ</b>\n\n{hw_text}\n\n"
        f"✅ Текст обновлен!\n\nПроверьте и выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer("Текст обновлен!")


@router.callback_query(F.data == "digest_back_hw")
async def handle_back_hw(callback: CallbackQuery):
    notifier = get_weekly_digest_notifier()
    if not notifier:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    user_id = callback.from_user.id
    hw_text = notifier.pending_digests.get(user_id, {}).get("hw_text", "")
    
    if not hw_text:
        hw_text = notifier.format_homework_digest()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="digest_send_hw"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="digest_edit_hw")
        ],
        [
            InlineKeyboardButton(text="⏭️ Пропустить ДЗ", callback_data="digest_skip_hw")
        ]
    ])
    
    await callback.message.edit_text(
        f"📢 <b>Еженедельный дайджест ДЗ</b>\n\n{hw_text}\n\n"
        f"Проверьте и выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "digest_add_hw")
async def handle_add_hw_from_digest(callback: CallbackQuery):
    await callback.answer(
        "Используйте /homework для добавления ДЗ, затем вернитесь сюда и нажмите 'Обновить текст'",
        show_alert=True
    )


@router.callback_query(F.data == "digest_del_hw")
async def handle_del_hw_from_digest(callback: CallbackQuery):
    await callback.answer(
        "Используйте /homework -> Управление для удаления ДЗ, затем вернитесь и нажмите 'Обновить текст'",
        show_alert=True
    )


async def _send_km_digest(callback: CallbackQuery, notifier: WeeklyDigestNotifier, user_id: int):
    km_text = notifier.pending_digests.get(user_id, {}).get("km_text", "")
    if not km_text:
        km_text = notifier.format_control_measures_digest()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="digest_send_km"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="digest_edit_km")
        ],
        [
            InlineKeyboardButton(text="⏭️ Пропустить КМ", callback_data="digest_skip_km")
        ]
    ])
    
    await callback.message.answer(
        f"📢 <b>Еженедельный дайджест КМ</b>\n\n{km_text}\n\n"
        f"Проверьте и выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "digest_send_km")
async def handle_send_km_digest(callback: CallbackQuery):
    notifier = get_weekly_digest_notifier()
    if not notifier:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    user_id = callback.from_user.id
    km_text = notifier.pending_digests.get(user_id, {}).get("km_text", "")
    if not km_text:
        km_text = notifier.format_control_measures_digest()
    
    await callback.message.edit_text(
        f"{km_text}\n\n⏳ <b>Отправка подписчикам...</b>",
        parse_mode="HTML"
    )
    
    success, failed = await notifier.send_digest_to_subscribers("control_works", km_text)
    
    if user_id in notifier.pending_digests:
        notifier.pending_digests[user_id]["km_sent"] = True
        del notifier.pending_digests[user_id]
    
    await callback.message.edit_text(
        f"{km_text}\n\n"
        f"✅ <b>Дайджест КМ отправлен!</b>\n"
        f"Доставлено: {success} | Ошибок: {failed}\n\n"
        f"🎉 Еженедельная рассылка завершена!",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "digest_skip_km")
async def handle_skip_km_digest(callback: CallbackQuery):
    notifier = get_weekly_digest_notifier()
    if notifier:
        user_id = callback.from_user.id
        if user_id in notifier.pending_digests:
            del notifier.pending_digests[user_id]
    
    await callback.message.edit_text(
        "⏭️ Рассылка КМ пропущена.\n\n"
        "🎉 Еженедельная рассылка завершена!"
    )
    await callback.answer()


@router.callback_query(F.data == "digest_edit_km")
async def handle_edit_km_digest(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить КМ", callback_data="digest_add_km")],
        [InlineKeyboardButton(text="➖ Удалить КМ", callback_data="digest_del_km")],
        [InlineKeyboardButton(text="🔄 Обновить текст", callback_data="digest_refresh_km")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="digest_back_km")]
    ])
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "digest_refresh_km")
async def handle_refresh_km(callback: CallbackQuery):
    notifier = get_weekly_digest_notifier()
    if not notifier:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    user_id = callback.from_user.id
    km_text = notifier.format_control_measures_digest()
    
    if user_id in notifier.pending_digests:
        notifier.pending_digests[user_id]["km_text"] = km_text
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="digest_send_km"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="digest_edit_km")
        ],
        [
            InlineKeyboardButton(text="⏭️ Пропустить КМ", callback_data="digest_skip_km")
        ]
    ])
    
    await callback.message.edit_text(
        f"📢 <b>Еженедельный дайджест КМ</b>\n\n{km_text}\n\n"
        f"✅ Текст обновлен!\n\nПроверьте и выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer("Текст обновлен!")


@router.callback_query(F.data == "digest_back_km")
async def handle_back_km(callback: CallbackQuery):
    notifier = get_weekly_digest_notifier()
    if not notifier:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    user_id = callback.from_user.id
    km_text = notifier.pending_digests.get(user_id, {}).get("km_text", "")
    
    if not km_text:
        km_text = notifier.format_control_measures_digest()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="digest_send_km"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="digest_edit_km")
        ],
        [
            InlineKeyboardButton(text="⏭️ Пропустить КМ", callback_data="digest_skip_km")
        ]
    ])
    
    await callback.message.edit_text(
        f"📢 <b>Еженедельный дайджест КМ</b>\n\n{km_text}\n\n"
        f"Проверьте и выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "digest_add_km")
async def handle_add_km_from_digest(callback: CallbackQuery):
    await callback.answer(
        "Используйте /homework для добавления КМ, затем вернитесь и нажмите 'Обновить текст'",
        show_alert=True
    )


@router.callback_query(F.data == "digest_del_km")
async def handle_del_km_from_digest(callback: CallbackQuery):
    await callback.answer(
        "Используйте /homework -> Управление для удаления КМ, затем вернитесь и нажмите 'Обновить текст'",
        show_alert=True
    )

from aiogram.filters import Command
from aiogram.enums import ChatType


@router.message(Command("test_digest"))
async def cmd_test_digest(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    
    member = group_manager.get_member(message.from_user.id)
    if not member or member.get("role") not in ["Староста", "Зам старосты", "Профорг"]:
        await message.answer("⛔ Эта команда доступна только старосте и профоргу.")
        return
    
    notifier = get_weekly_digest_notifier()
    if not notifier:
        await message.answer("❌ Система дайджестов не инициализирована. Перезапустите бота.")
        return
    
    hw_text = notifier.format_homework_digest()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="digest_send_hw"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="digest_edit_hw")
        ],
        [
            InlineKeyboardButton(text="⏭️ Пропустить ДЗ", callback_data="digest_skip_hw")
        ]
    ])
    
    user_id = message.from_user.id
    notifier.pending_digests[user_id] = {
        "hw_text": hw_text,
        "km_text": notifier.format_control_measures_digest(),
        "hw_sent": False,
        "km_sent": False
    }
    
    await message.answer(
        f"🧪 <b>ТЕСТОВЫЙ РЕЖИМ - Еженедельный дайджест ДЗ</b>\n\n"
        f"{hw_text}\n\n"
        f"Проверьте и выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(Command("digest_preview"))
async def cmd_digest_preview(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    
    member = group_manager.get_member(message.from_user.id)
    if not member or member.get("role") not in ["Староста", "Зам старосты", "Профорг"]:
        await message.answer("⛔ Эта команда доступна только старосте и профоргу.")
        return
    
    notifier = get_weekly_digest_notifier()
    if not notifier:
        await message.answer("❌ Система дайджестов не инициализирована.")
        return
    
    hw_text = notifier.format_homework_digest()
    km_text = notifier.format_control_measures_digest()
    
    await message.answer(
        f"👀 <b>Предпросмотр дайджеста</b>\n\n"
        f"{'─' * 30}\n\n"
        f"{hw_text}\n\n"
        f"{'─' * 30}\n\n"
        f"{km_text}",
        parse_mode="HTML"
    )
