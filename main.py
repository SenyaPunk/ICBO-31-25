import os 
from dotenv import *

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from commands.utils.start import router as start_router
from commands.utils.help import router as help_router
from commands.utils.hello import router as hello_router

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
