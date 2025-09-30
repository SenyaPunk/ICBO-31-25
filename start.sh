#!/bin/bash

# Скрипт быстрого старта для Telegram бота

echo "🚀 Запуск Telegram бота для университетской группы"
echo ""

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не установлен. Установите Python 3.8 или новее."
    exit 1
fi

echo "✅ Python найден: $(python3 --version)"

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден. Создаю из .env.example..."
    cp .env.example .env
    echo "📝 Пожалуйста, отредактируйте файл .env и добавьте ваш BOT_TOKEN"
    echo "   Получите токен у @BotFather в Telegram"
    exit 1
fi

# Проверка наличия виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создаю виртуальное окружение..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "🔧 Активирую виртуальное окружение..."
source venv/bin/activate

# Установка зависимостей
echo "📥 Устанавливаю зависимости..."
pip install -r requirements.txt --quiet

# Проверка токена
if grep -q "your_bot_token_here" .env; then
    echo "❌ Пожалуйста, добавьте ваш BOT_TOKEN в файл .env"
    echo "   Получите токен у @BotFather в Telegram"
    exit 1
fi

echo ""
echo "✅ Все готово! Запускаю бота..."
echo "   Нажмите Ctrl+C для остановки"
echo ""

# Запуск бота
python3 main.py
