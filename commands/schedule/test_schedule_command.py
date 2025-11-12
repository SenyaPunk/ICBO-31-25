from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime, timedelta
from dateutil import tz
import logging
import os

from commands.group.group_manager import GroupManager, Role
from commands.schedule.notifier_instance import get_notifier

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("test_schedule"))
async def test_schedule_command(message: Message):
        
    test_mode = os.environ.get("TEST_MODE", "false").lower() == "true"
    if not test_mode:
        await message.reply(
            "⚠️ Тестовый режим не активен.\n\n"
            "Чтобы включить тестовый режим, добавьте в .env:\n"
            "<code>TEST_MODE=true\n"
            "TEST_CHECK_INTERVAL=10  # проверка каждые 10 секунд\n"
            "TEST_NOTIFY_MINUTES=1  # уведомление за 1 минуту</code>",
            parse_mode="HTML"
        )
        return
    
    group_manager = GroupManager()
    member = group_manager.get_member(message.from_user.id)
    
    if not member:
        await message.reply("❌ Вы не зарегистрированы в системе группы.")
        return
    
    if member.get("role") != Role.STAROSTA.value:
        await message.reply("❌ Эта команда доступна только старосте группы.")
        return
    
    schedule_notifier = get_notifier()
    
    if not schedule_notifier or not schedule_notifier.is_running:
        await message.reply(
            "❌ Система уведомлений не запущена.\n\n"
            f"<b>Отладочная информация:</b>\n"
            f"• schedule_notifier: {'найден' if schedule_notifier else 'None'}\n"
            f"• is_running: {schedule_notifier.is_running if schedule_notifier else 'N/A'}\n\n"
            "Убедитесь, что бот полностью запущен и переменная NOTIFICATION_CHAT_ID установлена в .env "
            "(или TEST_MODE=true для тестирования без чата).",
            parse_mode="HTML"
        )
        return
    
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    tz_moscow = tz.gettz("Europe/Moscow")
    
    if not args:
        current = schedule_notifier.get_current_time()
        await message.reply(
            f"🕐 <b>Текущее тестовое время:</b>\n"
            f"{current.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"<b>Настройки:</b>\n"
            f"• Проверка каждые {schedule_notifier.check_interval}с\n"
            f"• Уведомление за {schedule_notifier.notify_minutes_before}мин\n\n"
            f"<b>Примеры использования:</b>\n"
            f"<code>/test_schedule 2025-11-12 14:10</code>\n"
            f"<code>/test_schedule today 14:10</code>\n"
            f"<code>/test_schedule now</code> - сбросить",
            parse_mode="HTML"
        )
        return
    
    if args[0].lower() == "now":
        schedule_notifier.test_current_time = None
        now = datetime.now(tz_moscow)
        await message.reply(
            f"✅ Тестовое время сброшено на реальное:\n"
            f"{now.strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="HTML"
        )
        return
    
    try:
        if len(args) >= 2:
            date_str = args[0]
            time_str = args[1]
            
            if date_str.lower() == "today":
                date_str = datetime.now(tz_moscow).strftime("%Y-%m-%d")
            
            datetime_str = f"{date_str} {time_str}"
            test_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            test_time = test_time.replace(tzinfo=tz_moscow)
            
            schedule_notifier.set_test_time(test_time)
            
            notify_time = test_time + timedelta(minutes=schedule_notifier.notify_minutes_before)
            
            await message.reply(
                f"✅ <b>Тестовое время установлено:</b>\n"
                f"🕐 {test_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"<b>Уведомления будут приходить о парах, которые начинаются в:</b>\n"
                f"🔔 {notify_time.strftime('%H:%M')}\n\n"
                f"<i>Проверка происходит каждые {schedule_notifier.check_interval} секунд.</i>\n\n"
                f"💡 <b>Совет:</b> Посмотрите расписание командой /schedule и установите время "
                f"за {schedule_notifier.notify_minutes_before} минут до начала нужной пары.",
                parse_mode="HTML"
            )
        else:
            await message.reply(
                "❌ Неверный формат команды.\n\n"
                "<b>Примеры:</b>\n"
                "<code>/test_schedule 2025-11-12 14:10</code>\n"
                "<code>/test_schedule today 14:10</code>\n"
                "<code>/test_schedule now</code>",
                parse_mode="HTML"
            )
    except ValueError as e:
        await message.reply(
            f"❌ Ошибка при парсинге даты/времени: {e}\n\n"
            "<b>Формат:</b> <code>/test_schedule ГГГГ-ММ-ДД ЧЧ:ММ</code>\n"
            "<b>Пример:</b> <code>/test_schedule 2025-11-12 14:10</code>",
            parse_mode="HTML"
        )
