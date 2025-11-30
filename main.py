import os 
from dotenv import *

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeDefault

from commands.utils.start import router as start_router
from commands.utils.help import router as help_router
from commands.utils.hello import router as hello_router
from commands.utils.myid import router as myid_router  
from commands.notifications.notifications import router as notifications_router
from commands.notifications.notifications_command import router as notifications_command_router
from commands.notifications.notification_panel_command import router as notification_panel_router
from commands.group.admin_command import router as admin_router
from commands.schedule.schedule_command import router as schedule_router
from commands.schedule.attendance_handler import router as attendance_router
from commands.schedule.file_manager_command import router as file_manager_router
from commands.schedule.test_schedule_command import router as test_schedule_router
from commands.schedule.schedule_notifier import ScheduleNotifier
from commands.schedule import notifier_instance
from commands.greetings.greetings_command import router as greetings_router
from commands.greetings.greetings_command import setup_scheduler as setup_greetings_scheduler
from commands.greetings.greetings_command import start_scheduler as start_greetings_scheduler
from commands.schedule.headman_checker import (
    router as headman_checker_router,
    HeadmanChecker,
    set_headman_checker
)
from commands.schedule.birthday_notifier import (
    BirthdayNotifier,
    set_birthday_notifier
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(hello_router)
    dp.include_router(myid_router)  
    dp.include_router(notifications_router)
    dp.include_router(notifications_command_router)
    dp.include_router(notification_panel_router)
    dp.include_router(admin_router)
    dp.include_router(schedule_router)
    dp.include_router(attendance_router)
    dp.include_router(file_manager_router)
    dp.include_router(test_schedule_router)
    dp.include_router(greetings_router)
    dp.include_router(headman_checker_router)
    
    commands = [
        BotCommand(command="start", description="🏠 Главное меню / Регистрация"),
        BotCommand(command="help", description="❓ Помощь"),
        BotCommand(command="hello", description="👋 Поздороваться"),
        BotCommand(command="schedule", description="📚 Расписание на неделю"),
        BotCommand(command="today", description="📚 Расписание на сегодня"),
        BotCommand(command="notifications", description="🔔 Настройки уведомлений"),
        BotCommand(command="notif_panel", description="📢 Панель уведомлений (Староста)"),
        BotCommand(command="admin", description="👨‍💼 Панель администратора"),
        BotCommand(command="myid", description="🆔 Узнать свой ID"),
        BotCommand(command="manage_files", description="📂 Управление файлов для пар (Староста)"),
        BotCommand(command="test_schedule", description="🧪 Тест уведомлений (Староста)"),
        BotCommand(command="preview", description="👀 Предпросмотр приветствия (Админ)"),
        BotCommand(command="greeting_schedule", description="📅 Расписание приветствий (Админ)"),
        BotCommand(command="greeting_config", description="⚙️ Настройки приветствий (Админ)")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    
    logger.info("Бот запущен и готов к работе!")
    
    setup_greetings_scheduler(bot)
    start_greetings_scheduler()
    logger.info("✅ Система приветствий инициализирована")
    
    schedule_notifier = ScheduleNotifier(bot)
    notifier_instance.set_notifier(schedule_notifier)
    logger.info("ScheduleNotifier создан и зарегистрирован")
    
    notification_chat_id = os.environ.get("NOTIFICATION_CHAT_ID")
    test_mode = os.environ.get("TEST_MODE", "false").lower() == "true"
    
    if notification_chat_id or test_mode:
        chat_id_for_checker = notification_chat_id or "test"
        headman_checker = HeadmanChecker(bot, chat_id_for_checker)
        set_headman_checker(headman_checker)
        schedule_notifier.set_headman_checker(headman_checker)
        logger.info(f"HeadmanChecker создан и подключен (chat_id: {chat_id_for_checker})")
    else:
        logger.warning("NOTIFICATION_CHAT_ID не установлен и TEST_MODE не активен. HeadmanChecker не будет работать.")
    
    birthday_notifier = BirthdayNotifier(bot)
    set_birthday_notifier(birthday_notifier)
    logger.info("BirthdayNotifier создан и зарегистрирован")
    
    notifier_task = asyncio.create_task(schedule_notifier.start())
    logger.info(f"ScheduleNotifier запущен, is_running={schedule_notifier.is_running}")
    
    birthday_task = asyncio.create_task(birthday_notifier.start())
    logger.info("BirthdayNotifier запущен")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        schedule_notifier.stop()
        birthday_notifier.stop()  
        notifier_task.cancel()
        birthday_task.cancel()  
        try:
            await notifier_task
        except asyncio.CancelledError:
            pass
        try:
            await birthday_task
        except asyncio.CancelledError:
            pass
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
