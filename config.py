import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота от @BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN')

# ID администратора (ваш Telegram ID)
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# Информация о группе
GROUP_INFO = {
    'name': 'Группа ИВТ-301',
    'course': '3 курс',
    'faculty': 'Факультет информационных технологий',
    'students_count': 25
}

# URL вашего веб-приложения (после деплоя на Vercel)
WEB_APP_URL = os.getenv('WEB_APP_URL', 'https://your-app.vercel.app')
