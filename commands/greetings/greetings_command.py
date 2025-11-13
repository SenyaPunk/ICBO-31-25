import os
import logging
from typing import Literal
import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from utils.fusion_brain import FusionBrainAPI
from utils.text_generator import TextGenerator
from commands.schedule.schedule_parser import fetch_ics_from_json, parse_schedule, extract_teacher_name, URL
import re

router = Router()
logger = logging.getLogger(__name__)

ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
NOTIFICATION_CHAT_ID = os.getenv('NOTIFICATION_CHAT_ID', '0')

text_gen = TextGenerator(
    api_url=os.getenv('WISPBYTE_API_URL'),
    api_key=os.getenv('WISPBYTE_API_KEY')
)

fusion_api_key = os.getenv('FUSION_API_KEY')
fusion_secret_key = os.getenv('FUSION_SECRET_KEY')

if not fusion_api_key or not fusion_secret_key:
    logger.warning("Fusion Brain API ключи не найдены. Изображения генерироваться не будут.")
    fusion_api = None
else:
    fusion_api = FusionBrainAPI(
        url='https://api-key.fusionbrain.ai/',
        api_key=fusion_api_key,
        secret_key=fusion_secret_key
    )

scheduler = AsyncIOScheduler()


def get_image_prompt(kind: Literal["morning", "evening"]) -> str:
    if kind == "morning":
        return (
            "Милый пушистый котёнок утром, мягкий тёплый свет, "
            "солнечные лучи, уют, высокое качество, иллюстрация, "
            "детальная шерсть, 4k, warm tones"
        )
    else:
        return (
            "Милый котёнок спокойно спит под пледом, лунный свет из окна, "
            "мягкие тени, уютная атмосфера, высокое качество, "
            "иллюстрация, 4k, night, dreamy"
        )


def get_tomorrow_schedule() -> str:
    try:
        ical_str = fetch_ics_from_json(URL)
        events = parse_schedule(ical_str)
        
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        tomorrow_events = sorted(
            [e for e in events if e["start"].date() == tomorrow],
            key=lambda x: x["start"]
        )
        
        if not tomorrow_events:
            return "\n\n📅 <b>Завтра пар нет! Можно отдыхать! 🎉</b>"
        
        schedule_text = f"\n\n📅 <b>Расписание на завтра ({tomorrow.strftime('%d.%m.%Y')}):</b>\n"
        
        for i, e in enumerate(tomorrow_events, 1):
            time_str = f"{e['start'].strftime('%H:%M')} - {e['end'].strftime('%H:%M')}"
            match = re.match(r'^(ЛК|ПР|ЛАБ)\s+(.+)', e['title'])
            lesson_type, title = (match.group(1), match.group(2)) if match else ("", e['title'])
            
            schedule_text += f"\n<b>{i}️⃣  {lesson_type} {title}</b>\n"
            schedule_text += f"🕐 {time_str}"
            
            if e['location']:
                schedule_text += f"  •  📍 {e['location']}\n"
            else:
                schedule_text += "\n"
            
            teacher = extract_teacher_name(e['teacher'])
            if teacher:
                schedule_text += f"👤 {teacher}\n"
        
        return schedule_text
        
    except Exception as e:
        logger.error(f"Ошибка получения расписания на завтра: {e}", exc_info=True)
        return "\n\n📅 <b>Не удалось загрузить расписание на завтра</b>"


async def send_greeting_message(bot, kind: Literal["morning", "evening"]):
    if NOTIFICATION_CHAT_ID == '0':
        logger.warning("NOTIFICATION_CHAT_ID не установлен")
        return

    try:
        logger.info(f"Генерируем текст для {kind} приветствия...")
        text = text_gen.generate_greeting(kind)
        
        if not text or len(text.strip()) == 0:
            logger.error("Сгенерированный текст пустой!")
            text = "Доброе утро! 🌅" if kind == "morning" else "Спокойной ночи! 🌙"
        
        if kind == "evening":
            schedule_text = get_tomorrow_schedule()
            text = text + schedule_text
        
        if len(text) > 1024:
            logger.warning(f"Текст слишком длинный ({len(text)} символов), обрезаем до 1020")
            text = text[:1020] + "..."
        
        if fusion_api:
            logger.info(f"Генерируем изображение для {kind}...")
            image_prompt = get_image_prompt(kind)
            image_bytes = fusion_api.generate_image_bytes(image_prompt)
            
            if image_bytes:
                logger.info(f"Отправляем фото с caption")
                photo = BufferedInputFile(image_bytes, filename="greeting.jpg")
                await bot.send_photo(
                    chat_id=NOTIFICATION_CHAT_ID,
                    photo=photo,
                    caption=text,
                    parse_mode="HTML"
                )
                logger.info(f"✅ Отправлено {kind} приветствие в чат {NOTIFICATION_CHAT_ID}")
                return
        
        logger.warning(f"Отправляем только текст без изображения")
        await bot.send_message(
            chat_id=NOTIFICATION_CHAT_ID,
            text=f"{text}\n\n(Изображение временно недоступно)",
            parse_mode="HTML"
        )
        logger.warning(f"Отправлено {kind} приветствие без изображения")
            
    except Exception as e:
        logger.error(f"Ошибка отправки приветствия: {e}", exc_info=True)


@router.message(Command("preview"))
async def preview_greeting(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ Только администратор может использовать эту команду.")
        return
    
    args = message.text.split()
    kind = "morning"
    
    if len(args) > 1:
        arg = args[1].lower()
        if arg in ("evening", "night", "вечер", "ночь"):
            kind = "evening"
    
    await message.reply(
        "Готовлю для вас пост... ☕️🐾" if kind == "morning" 
        else "Готовлю уютный вечерний пост... 🌙🐾"
    )
    
    try:
        text = text_gen.generate_greeting(kind)
        
        if not text or len(text.strip()) == 0:
            text = "Доброе утро! 🌅" if kind == "morning" else "Спокойной ночи! 🌙"
        
        if kind == "evening":
            schedule_text = get_tomorrow_schedule()
            text = text + schedule_text
        
        if len(text) > 1024:
            text = text[:1020] + "..."
        
        if fusion_api:
            image_prompt = get_image_prompt(kind)
            image_bytes = fusion_api.generate_image_bytes(image_prompt)
            
            if image_bytes:
                photo = BufferedInputFile(image_bytes, filename="preview.jpg")
                await message.answer_photo(photo=photo, caption=text, parse_mode="HTML")
                return
        
        await message.answer(
            f"{text}\n\n(Изображение временно недоступно)\n\n"
            f"💡 Настройте FUSION_API_KEY и FUSION_SECRET_KEY в .env файле",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка предпросмотра: {e}", exc_info=True)
        await message.answer("Не удалось создать превью, попробуйте позже.")


@router.message(Command("greeting_schedule"))
async def show_greeting_schedule(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ Только администратор может использовать эту команду.")
        return
    
    morning_time = os.getenv('MORNING_TIME', '08:00')
    evening_time = os.getenv('EVENING_TIME', '22:00')
    
    await message.answer(
        f"📅 <b>Расписание приветствий:</b>\n\n"
        f"🌅 Доброе утро: {morning_time}\n"
        f"🌙 Спокойной ночи: {evening_time}\n"
        f"   (с расписанием на следующий день)\n\n"
        f"Чат: {NOTIFICATION_CHAT_ID}\n\n"
        f"Для изменения расписания отредактируйте переменные окружения "
        f"MORNING_TIME и EVENING_TIME в формате HH:MM",
        parse_mode="HTML"
    )


@router.message(Command("greeting_config"))
async def check_greeting_config(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ Только администратор может использовать эту команду.")
        return
    
    status = []
    
    bot_token = os.getenv('BOT_TOKEN')
    status.append(f"🤖 BOT_TOKEN: {'✅ Настроен' if bot_token else '❌ Не найден'}")
    
    fusion_key = os.getenv('FUSION_API_KEY')
    fusion_secret = os.getenv('FUSION_SECRET_KEY')
    status.append(f"🎨 FUSION_API_KEY: {'✅ Настроен' if fusion_key else '❌ Не найден'}")
    status.append(f"🔑 FUSION_SECRET_KEY: {'✅ Настроен' if fusion_secret else '❌ Не найден'}")
    
    wispbyte_url = os.getenv('WISPBYTE_API_URL')
    wispbyte_key = os.getenv('WISPBYTE_API_KEY')
    status.append(f"🌐 WISPBYTE_API_URL: {'✅ ' + wispbyte_url if wispbyte_url else '❌ Не найден'}")
    status.append(f"🔐 WISPBYTE_API_KEY: {'✅ Настроен' if wispbyte_key else '❌ Не найден'}")
    
    status.append(f"💬 NOTIFICATION_CHAT_ID: {'✅ ' + NOTIFICATION_CHAT_ID if NOTIFICATION_CHAT_ID != '0' else '❌ Не настроен'}")
    
    status.append(f"👨‍💼 ADMIN_ID: {'✅ ' + str(ADMIN_ID) if ADMIN_ID != 0 else '❌ Не настроен'}")
    
    morning = os.getenv('MORNING_TIME', '08:00')
    evening = os.getenv('EVENING_TIME', '22:00')
    status.append(f"⏰ MORNING_TIME: {morning}")
    status.append(f"🌙 EVENING_TIME: {evening}")
    
    config_text = "<b>Конфигурация системы приветствий:</b>\n\n" + "\n".join(status)
    
    if not fusion_key or not fusion_secret:
        config_text += "\n\n⚠️ <b>Внимание!</b> Fusion Brain API не настроен.\n"
        config_text += "Изображения генерироваться не будут."
    
    if not wispbyte_url or not wispbyte_key:
        config_text += "\n\n⚠️ <b>Внимание!</b> Wispbyte API не настроен.\n"
        config_text += "Будут использоваться стандартные тексты.\n"
        config_text += "Настройте WISPBYTE_API_URL и WISPBYTE_API_KEY в .env файле."
    
    if NOTIFICATION_CHAT_ID == '0':
        config_text += "\n\n⚠️ <b>Внимание!</b> NOTIFICATION_CHAT_ID не настроен.\n"
        config_text += "Автоматическая отправка не будет работать."
    
    await message.answer(config_text, parse_mode="HTML")


def setup_scheduler(bot):
    morning_time = os.getenv('MORNING_TIME', '08:00')
    evening_time = os.getenv('EVENING_TIME', '22:00')
    
    morning_hour, morning_minute = map(int, morning_time.split(':'))
    evening_hour, evening_minute = map(int, evening_time.split(':'))
    
    scheduler.add_job(
        send_greeting_message,
        CronTrigger(hour=morning_hour, minute=morning_minute),
        args=[bot, "morning"],
        id="morning_greeting",
        replace_existing=True
    )
    
    scheduler.add_job(
        send_greeting_message,
        CronTrigger(hour=evening_hour, minute=evening_minute),
        args=[bot, "evening"],
        id="evening_greeting",
        replace_existing=True
    )
    
    logger.info(f"✅ Планировщик приветствий настроен: утро - {morning_time}, вечер - {evening_time}")


def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("✅ Планировщик приветствий запущен")
