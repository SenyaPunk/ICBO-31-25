import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from aiogram import Bot, Router
from commands.group.group_manager import group_manager

logger = logging.getLogger(__name__)
router = Router()


class BirthdayNotifier:
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.check_interval = 60 
        logger.info("BirthdayNotifier инициализирован")
    
    async def start(self):
        self.is_running = True
        logger.info("BirthdayNotifier запущен")
        
        while self.is_running:
            try:
                await self._check_birthdays()
            except Exception as e:
                logger.error(f"Ошибка при проверке дней рождения: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        self.is_running = False
        logger.info("BirthdayNotifier остановлен")
    
    async def _check_birthdays(self):
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        is_evening_time = current_hour == 20 and current_minute == 0
        is_morning_time = current_hour == 8 and current_minute == 0
        
        if not is_evening_time and not is_morning_time:
            return
        
        headman = group_manager.get_headman()
        if not headman:
            logger.debug("Староста не найден, пропускаем проверку дней рождения")
            return
        
        headman_id = headman.get("user_id")
        if not headman_id:
            logger.warning("У старосты отсутствует user_id")
            return
        
        all_members = group_manager.get_all_members()
        
        today = now.date()
        tomorrow = today + timedelta(days=1)
        
        for user_id, member in all_members.items():
            birth_date_str = member.get("birth_date")
            if not birth_date_str:
                continue
            
            try:
                birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y").date()
                
                birth_day = birth_date.day
                birth_month = birth_date.month
                
                member_name = member.get("full_name", "Неизвестный")
                
                if is_evening_time:
                    if tomorrow.day == birth_day and tomorrow.month == birth_month:
                        if str(headman_id) != str(user_id):
                            await self._send_eve_notification(headman_id, member_name, birth_date_str)
                
                if is_morning_time:
                    if today.day == birth_day and today.month == birth_month:
                        if str(headman_id) != str(user_id):
                            await self._send_birthday_notification(headman_id, member_name, birth_date_str)
                        
            except ValueError as e:
                logger.warning(f"Некорректный формат даты рождения у пользователя {user_id}: {birth_date_str}")
                continue
    
    async def _send_eve_notification(self, headman_id: int, member_name: str, birth_date: str):
        try:
            birth = datetime.strptime(birth_date, "%d.%m.%Y")
            tomorrow = datetime.now() + timedelta(days=1)
            age = tomorrow.year - birth.year
            
            message = (
                f"🎂 <b>Напоминание о дне рождения!</b>\n\n"
                f"Завтра день рождения у <b>{member_name}</b>!\n"
                f"Исполняется <b>{age}</b> лет.\n\n"
                f"Не забудь подготовить поздравление! 🎁"
            )
            
            await self.bot.send_message(
                chat_id=headman_id,
                text=message
            )
            logger.info(f"Отправлено уведомление о завтрашнем дне рождения: {member_name}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления о дне рождения (канун): {e}")
    
    async def _send_birthday_notification(self, headman_id: int, member_name: str, birth_date: str):
        try:
            birth = datetime.strptime(birth_date, "%d.%m.%Y")
            today = datetime.now()
            age = today.year - birth.year
            
            message = (
                f"🎉 <b>Сегодня день рождения!</b>\n\n"
                f"У <b>{member_name}</b> сегодня день рождения!\n"
                f"Исполнилось <b>{age}</b> лет.\n\n"
                f"Пора поздравлять! 🎈🎁"
            )
            
            await self.bot.send_message(
                chat_id=headman_id,
                text=message
            )
            logger.info(f"Отправлено уведомление о дне рождения: {member_name}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления о дне рождения: {e}")
    
    async def test_birthday_check(self):
        logger.info("Запуск тестовой проверки дней рождения...")
        
        headman = group_manager.get_headman()
        if not headman:
            logger.warning("Староста не найден для тестовой проверки")
            return
        
        headman_id = headman.get("user_id")
        all_members = group_manager.get_all_members()
        
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        found_birthdays = []
        
        for user_id, member in all_members.items():
            birth_date_str = member.get("birth_date")
            if not birth_date_str:
                continue
            
            try:
                birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y").date()
                birth_day = birth_date.day
                birth_month = birth_date.month
                
                member_name = member.get("full_name", "Неизвестный")
                
                if today.day == birth_day and today.month == birth_month:
                    found_birthdays.append(f"🎉 Сегодня: {member_name}")
                elif tomorrow.day == birth_day and tomorrow.month == birth_month:
                    found_birthdays.append(f"🎂 Завтра: {member_name}")
                    
            except ValueError:
                continue
        
        if found_birthdays:
            message = "📋 <b>Найденные дни рождения:</b>\n\n" + "\n".join(found_birthdays)
        else:
            message = "📋 Ближайших дней рождения не найдено (сегодня/завтра)"
        
        try:
            await self.bot.send_message(chat_id=headman_id, text=message)
            logger.info(f"Тестовое сообщение отправлено старосте: {found_birthdays}")
        except Exception as e:
            logger.error(f"Ошибка отправки тестового сообщения: {e}")


_birthday_notifier: Optional[BirthdayNotifier] = None


def set_birthday_notifier(notifier: BirthdayNotifier):
    global _birthday_notifier
    _birthday_notifier = notifier


def get_birthday_notifier() -> Optional[BirthdayNotifier]:
    return _birthday_notifier
