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
from commands.group.admin_command import router as admin_router

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
    dp.include_router(admin_router)
    
    commands = [
        BotCommand(command="start", description="🏠 Главное меню / Регистрация"),
        BotCommand(command="help", description="❓ Помощь"),
        BotCommand(command="hello", description="👋 Поздороваться"),
        BotCommand(command="notifications", description="🔔 Настройки уведомлений"),
        BotCommand(command="admin", description="👨‍💼 Панель администратора"),
        BotCommand(command="myid", description="🆔 Узнать свой ID")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    
    logger.info("Бот запущен и готов к работе!")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
