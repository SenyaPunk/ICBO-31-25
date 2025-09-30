# 🚀 Полное руководство по развертыванию

## Шаг 1: Подготовка бота

### 1.1 Создание бота в Telegram

1. Откройте [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Введите имя бота (например: "Группа ИВТ-301")
4. Введите username бота (например: "ivt301_bot")
5. Сохраните полученный токен

### 1.2 Настройка Python бота

1. Создайте файл `.env`:
\`\`\`env
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_id
WEB_APP_URL=https://your-app.vercel.app
\`\`\`

2. Установите зависимости:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

## Шаг 2: Деплой веб-приложения на Vercel

### Вариант A: Через v0 (Рекомендуется)

1. Нажмите кнопку **"Publish"** в правом верхнем углу
2. Выберите ваш Vercel аккаунт
3. Дождитесь завершения деплоя
4. Скопируйте URL приложения (например: `https://your-app.vercel.app`)

### Вариант B: Через GitHub и Vercel

1. Загрузите код на GitHub:
\`\`\`bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/your-repo.git
git push -u origin main
\`\`\`

2. Перейдите на [vercel.com](https://vercel.com)
3. Нажмите "New Project"
4. Импортируйте ваш GitHub репозиторий
5. Vercel автоматически определит Next.js
6. Нажмите "Deploy"
7. Скопируйте URL после деплоя

### Вариант C: Через Vercel CLI

1. Установите Vercel CLI:
\`\`\`bash
npm i -g vercel
\`\`\`

2. Войдите в аккаунт:
\`\`\`bash
vercel login
\`\`\`

3. Задеплойте проект:
\`\`\`bash
vercel
\`\`\`

4. Для продакшн деплоя:
\`\`\`bash
vercel --prod
\`\`\`

## Шаг 3: Обновление конфигурации бота

1. Откройте `.env` файл Python бота
2. Обновите `WEB_APP_URL`:
\`\`\`env
WEB_APP_URL=https://your-actual-app.vercel.app
\`\`\`

## Шаг 4: Настройка кнопки меню в BotFather

1. Откройте [@BotFather](https://t.me/BotFather)
2. Отправьте `/mybots`
3. Выберите вашего бота
4. Нажмите **"Bot Settings"**
5. Выберите **"Menu Button"**
6. Нажмите **"Edit Menu Button URL"**
7. Введите URL: `https://your-app.vercel.app`
8. Готово! Теперь у бота есть кнопка меню

## Шаг 5: Запуск бота

### На локальном компьютере:
\`\`\`bash
python main.py
\`\`\`

### На сервере (с использованием screen):
\`\`\`bash
screen -S telegram_bot
python main.py
# Нажмите Ctrl+A, затем D для выхода из screen
\`\`\`

### На сервере (с использованием systemd):

Создайте файл `/etc/systemd/system/telegram-bot.service`:
\`\`\`ini
[Unit]
Description=Telegram Bot for University Group
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 /path/to/bot/main.py
Restart=always

[Install]
WantedBy=multi-user.target
\`\`\`

Запустите:
\`\`\`bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
\`\`\`

## Шаг 6: Тестирование

1. Откройте Telegram
2. Найдите вашего бота по username
3. Отправьте `/start`
4. Нажмите кнопку "🚀 Открыть приложение"
5. Приложение должно открыться внутри Telegram

## 🔄 Обновление приложения

### Обновление веб-приложения:
1. Внесите изменения в код
2. Закоммитьте и запушьте на GitHub (если используете GitHub)
3. Vercel автоматически задеплоит новую версию
4. Или нажмите "Publish" в v0 снова

### Обновление бота:
1. Остановите бота (Ctrl+C или `systemctl stop telegram-bot`)
2. Внесите изменения в код
3. Запустите бота снова

## 🌐 Использование собственного домена

1. В Vercel перейдите в настройки проекта
2. Выберите "Domains"
3. Добавьте ваш домен
4. Настройте DNS записи согласно инструкциям Vercel
5. Обновите `WEB_APP_URL` в `.env` бота
6. Обновите URL в BotFather

## 📊 Мониторинг

### Логи Vercel:
- Перейдите в проект на vercel.com
- Откройте вкладку "Logs"
- Просматривайте логи в реальном времени

### Логи бота:
\`\`\`bash
# Если используете systemd
sudo journalctl -u telegram-bot -f

# Если используете screen
screen -r telegram_bot
\`\`\`

## 🆘 Частые проблемы

### Бот не отвечает
- Проверьте, что бот запущен
- Проверьте правильность токена в `.env`
- Проверьте логи на наличие ошибок

### Приложение не открывается
- Проверьте, что URL в `.env` правильный
- Убедитесь, что приложение задеплоено
- Проверьте URL в BotFather

### Ошибка 404 при открытии приложения
- Убедитесь, что деплой завершился успешно
- Проверьте URL в браузере
- Проверьте логи Vercel

## ✅ Чеклист перед запуском

- [ ] Бот создан в BotFather
- [ ] Токен бота добавлен в `.env`
- [ ] Веб-приложение задеплоено на Vercel
- [ ] URL приложения добавлен в `.env` бота
- [ ] URL приложения настроен в BotFather (Menu Button)
- [ ] Python бот запущен
- [ ] Протестирована команда `/start`
- [ ] Приложение открывается в Telegram
- [ ] Все страницы работают корректно
\`\`\`

```json file="" isHidden
