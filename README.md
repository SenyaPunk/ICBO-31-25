# Telegram Бот для Университетской Группы

Модульный Telegram бот для управления информацией университетской группы.

## 🚀 Установка

1. Установите зависимости:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. Создайте файл `.env` на основе `.env.example`:
\`\`\`bash
cp .env.example .env
\`\`\`

3. Получите токен бота у [@BotFather](https://t.me/BotFather) в Telegram

4. Заполните `.env` файл:
   - `BOT_TOKEN` - токен вашего бота
   - `ADMIN_ID` - ваш Telegram ID (можно узнать у [@userinfobot](https://t.me/userinfobot))

## 📁 Структура проекта

\`\`\`
telegram-bot-university/
├── main.py                 # Основной файл запуска бота
├── config.py              # Конфигурация и настройки
├── handlers/              # Обработчики команд
│   ├── __init__.py
│   ├── start.py          # Команда /start и главное меню
│   ├── schedule.py       # Расписание занятий
│   ├── homework.py       # Домашние задания
│   └── group_info.py     # Информация о группе
├── keyboards/             # Клавиатуры для бота
│   ├── __init__.py
│   └── inline.py         # Inline-кнопки
├── requirements.txt       # Зависимости
├── .env.example          # Пример файла с переменными окружения
└── README.md             # Документация
\`\`\`

## 🎯 Доступные команды

- `/start` - Главное меню с кнопками
- `/schedule` - Расписание занятий
- `/homework` - Домашние задания
- `/group` - Информация о группе

## ▶️ Запуск

\`\`\`bash
python main.py
\`\`\`

## 📝 Настройка

1. Отредактируйте `config.py` для изменения информации о группе
2. Обновите расписание в `handlers/schedule.py`
3. Добавьте домашние задания в `handlers/homework.py`
4. Добавьте полезные ссылки в `handlers/group_info.py`

## 🔧 Добавление новых команд

1. Создайте новый файл в папке `handlers/`
2. Создайте Router и добавьте обработчики
3. Импортируйте и зарегистрируйте роутер в `main.py`

Пример:
\`\`\`python
# handlers/new_command.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("new"))
async def cmd_new(message: Message):
    await message.answer("Новая команда!")
\`\`\`

## 📚 Используемые библиотеки

- **aiogram 3.4.1** - современная асинхронная библиотека для Telegram Bot API
- **python-dotenv** - управление переменными окружения
