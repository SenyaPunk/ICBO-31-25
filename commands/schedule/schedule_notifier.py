import asyncio
import json
import logging
import os
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dateutil import tz

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile, InputMediaDocument

from commands.schedule.schedule_parser import (
    fetch_ics_from_json,
    parse_schedule,
    extract_teacher_name,
    URL
)
from commands.schedule.schedule_storage import ScheduleStorage

logger = logging.getLogger(__name__)


class ScheduleNotifier:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.storage = ScheduleStorage()
        self.notification_chat_id = os.environ.get("NOTIFICATION_CHAT_ID")
        self.is_running = False
        self.tz_moscow = tz.gettz("Europe/Moscow")
        
        self.test_mode = os.environ.get("TEST_MODE", "false").lower() == "true"
        self.test_current_time = None  
        
        if self.test_mode:
            self.check_interval = int(os.environ.get("TEST_CHECK_INTERVAL", "10"))  
            self.notify_minutes_before = int(os.environ.get("TEST_NOTIFY_MINUTES", "1"))  
            logger.info(f"ТЕСТОВЫЙ РЕЖИМ АКТИВЕН: проверка каждые {self.check_interval}с, уведомление за {self.notify_minutes_before}мин")
        else:
            self.check_interval = 60  
            self.notify_minutes_before = 10  
    
        self.notify_minutes_before_long_break = 30
        
        self.headman_checker = None
    
    def set_headman_checker(self, checker):
        self.headman_checker = checker
        logger.info("HeadmanChecker подключен к ScheduleNotifier")

    def set_test_time(self, test_time: datetime):
        if self.test_mode:
            self.test_current_time = test_time
            self.storage.clear_notified_lessons()
            logger.info(f"Установлено тестовое время: {test_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("Список уведомленных пар очищен для тестирования")
        else:
            logger.warning("Тестовое время можно установить только в тестовом режиме (TEST_MODE=true)")
    
    def get_current_time(self) -> datetime:
        if self.test_mode and self.test_current_time:
            return self.test_current_time
        return datetime.now(self.tz_moscow)
        
    async def start(self):
        if not self.notification_chat_id and not self.test_mode:
            logger.warning("NOTIFICATION_CHAT_ID не установлен. Уведомления не будут работать.")
            return
        
        if not self.notification_chat_id:
            logger.warning("NOTIFICATION_CHAT_ID не установлен, но тестовый режим активен.")
            
        self.is_running = True
        logger.info("Система уведомлений о парах запущена")
        
        while self.is_running:
            try:
                await self._check_and_notify()
            except Exception as e:
                logger.error(f"Ошибка в системе уведомлений: {e}", exc_info=True)
            
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        self.is_running = False
        logger.info("Система уведомлений остановлена")
    
    async def _check_and_notify(self):
        try:
            now = self.get_current_time()
            
            logger.info(f"Проверка расписания. Время: {now.strftime('%H:%M:%S')}")
            
            ical_str = fetch_ics_from_json(URL)
            events = parse_schedule(ical_str)
            
            today_events = [e for e in events if e["start"].date() == now.date()]
            today_events = sorted(today_events, key=lambda x: x["start"])
            logger.info(f"Найдено {len(today_events)} пар на сегодня")
            
            for event in today_events:
                start_time = event["start"]
                
                notify_minutes = self._get_notify_minutes_for_lesson(event, today_events)
                
                time_diff = (start_time - now).total_seconds() / 60
                
                min_diff = notify_minutes - 1
                max_diff = notify_minutes + 1
                
                if self.test_mode:
                    logger.info(f"  Пара: '{event['title']}' в {start_time.strftime('%H:%M')}, разница: {time_diff:.1f} мин (нужно {min_diff}-{max_diff})")
                
                if min_diff <= time_diff <= max_diff:
                    logger.info(f"  >>> НАЙДЕНА ПАРА ДЛЯ УВЕДОМЛЕНИЯ: {event['title']}")
                    lesson_full_id = f"{start_time.strftime('%Y%m%d%H%M')}_{event['title']}"
                    lesson_id = hashlib.md5(lesson_full_id.encode()).hexdigest()[:16]
                    
                    if not self.storage.was_notified(lesson_id):
                        if self.notification_chat_id:
                            await self._send_lesson_notification(event, lesson_id, lesson_full_id, notify_minutes)
                        else:
                            logger.info(f"Найдена пара для уведомления (нет CHAT_ID): {event['title']}")
                        
                        if self.headman_checker:
                            end_time = event["end"]
                            lesson_time = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                            
                            title = event["title"]
                            match = re.match(r'^(ЛК|ПР|ЛАБ)\s+(.+)', title)
                            if match:
                                lesson_type = match.group(1)
                                lesson_name = match.group(2)
                                full_lesson_name = f"{lesson_type} {lesson_name}".strip()
                            else:
                                full_lesson_name = title
                            
                            logger.info(f"Вызываем headman_checker.ask_headman_presence для '{full_lesson_name}'")
                            await self.headman_checker.ask_headman_presence(
                                lesson_id=lesson_id,
                                lesson_name=full_lesson_name,
                                lesson_time=lesson_time
                            )
                            logger.info(f"Запрос старосте отправлен для пары: {full_lesson_name}")
                        else:
                            logger.warning("HeadmanChecker не подключен (self.headman_checker = None)")
                        
                        self.storage.mark_as_notified(lesson_id)
                    else:
                        logger.info(f"  Пара уже была уведомлена ранее: {lesson_id}")
                        
        except Exception as e:
            logger.error(f"Ошибка при проверке расписания: {e}", exc_info=True)
    
    async def _send_lesson_notification(self, event: Dict, lesson_id: str, lesson_full_id: str, notify_minutes: int = None):
        try:
            if notify_minutes is None:
                notify_minutes = self.notify_minutes_before
            
            title = event["title"]
            start_time = event["start"]
            end_time = event["end"]
            location = event["location"]
            teacher_raw = event["teacher"]
            teacher = extract_teacher_name(teacher_raw)
            
            match = re.match(r'^(ЛК|ПР|ЛАБ)\s+(.+)', title)
            if match:
                lesson_type = match.group(1)
                lesson_name = match.group(2)
            else:
                lesson_type = ""
                lesson_name = title
            
            type_emoji = {
                "ЛК": "📖",
                "ПР": "✏️",
                "ЛАБ": "🔬"
            }
            emoji = type_emoji.get(lesson_type, "📚")
            
            notify_text = f"Через {notify_minutes} минут" if notify_minutes > 1 else "Через 1 минуту"
            
            message_text = f"⏰ <b>{notify_text} начнется пара</b>\n\n"
            message_text += f"{emoji}  <b>{lesson_type} {lesson_name}</b>\n"
            message_text += f"🕐 {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
            
            if location:
                message_text += f"  •  📍 {location}"
            
            message_text += "\n"
            
            if teacher:
                message_text += f"👤 Преподаватель: <b>{teacher}</b>\n"
            
            if self.test_mode:
                message_text += f"\n<i>🧪 ТЕСТОВЫЙ РЕЖИМ</i>"
            
            full_subject = f"{lesson_type} {lesson_name}".strip() if lesson_type else lesson_name
            
            break_minutes = 10  
            if notify_minutes == self.notify_minutes_before_long_break:
                break_minutes = 30  

            logger.info(f"Сохраняем данные о паре: lesson_id={lesson_id}, full_subject='{full_subject}', lesson_name='{lesson_name}'")
            self.storage.save_attendance_message(
                lesson_id, 
                0,  
                lesson_name, 
                full_subject,
                lesson_start=start_time.isoformat(),
                break_minutes=break_minutes
            )
            logger.info(f"Данные сохранены в storage до отправки сообщения")

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="✋ Меня надо отметить на паре",
                    callback_data=f"att:{lesson_id}"
                )],
                [InlineKeyboardButton(
                    text="📝 Добавить ДЗ",
                    callback_data=f"quick_hw:{lesson_id}"
                )]
            ])
            
            logger.info(f"Ищем файлы для пары: '{title}'")
            files = self.storage.get_lesson_files(lesson_id, title)
            
            if files:
                logger.info(f"Найдено {len(files)} файлов для отправки")
                message_text += f"\n📎 Прикрепленные материалы: {len(files)} файл(ов)"
            
            sent_message = await self.bot.send_message(
                chat_id=self.notification_chat_id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            self.storage.save_attendance_message(
                lesson_id, 
                sent_message.message_id, 
                lesson_name, 
                full_subject,
                lesson_start=start_time.isoformat(),
                break_minutes=break_minutes
            )
            logger.info(f"Обновлен message_id={sent_message.message_id} для lesson_id={lesson_id}")
            logger.info(f"Отправлено уведомление о паре: {title} в {start_time.strftime('%H:%M')}")
            
            if files:
                try:
                    media_group = []
                    for i, file_path in enumerate(files):
                        if os.path.exists(file_path):
                            file = FSInputFile(file_path)
                            file_name = os.path.basename(file_path)
                            caption = f"📎 Материалы к паре" if i == 0 else None
                            media_group.append(InputMediaDocument(
                                media=file,
                                caption=caption
                            ))
                            logger.info(f"Добавлен файл в группу: {file_path}")
                        else:
                            logger.warning(f"Файл не существует: {file_path}")
                    
                    if media_group:
                        await self.bot.send_media_group(
                            chat_id=self.notification_chat_id,
                            media=media_group,
                            reply_to_message_id=sent_message.message_id
                        )
                        logger.info(f"Отправлена группа из {len(media_group)} файлов")
                except Exception as e:
                    logger.error(f"Ошибка при отправке группы файлов: {e}", exc_info=True)
            else:
                logger.info(f"Файлы для пары '{title}' не найдены")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления о паре: {e}", exc_info=True)

    async def get_attendance_list(self, lesson_id: str) -> List[Dict]:
        return self.storage.get_attendance_list(lesson_id)
    
    def _get_notify_minutes_for_lesson(self, event: Dict, today_events: List[Dict]) -> int:
        start_time = event["start"]
        
        prev_event = None
        for e in today_events:
            if e["end"] <= start_time and e != event:
                if prev_event is None or e["end"] > prev_event["end"]:
                    prev_event = e
        
        if prev_event:
            break_minutes = (start_time - prev_event["end"]).total_seconds() / 60
            
            if self.test_mode:
                logger.info(f"  Перерыв до пары '{event['title']}': {break_minutes:.0f} мин (предыдущая: '{prev_event['title']}' до {prev_event['end'].strftime('%H:%M')})")
            
            if 25 <= break_minutes <= 35:
                logger.info(f"  >>> 30-минутный перерыв обнаружен! Уведомление за {self.notify_minutes_before_long_break} минут")
                return self.notify_minutes_before_long_break
        else:
            if self.test_mode:
                logger.info(f"  Пара '{event['title']}' - первая пара дня, уведомление за {self.notify_minutes_before} минут")
        
        return self.notify_minutes_before
