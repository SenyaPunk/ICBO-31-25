# 📚 Примеры использования

## Примеры для Python бота

### Добавление новой команды

\`\`\`python
# handlers/exams.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from keyboards.inline import get_back_button

router = Router()

@router.message(Command("exams"))
async def cmd_exams(message: Message):
    """Показать расписание экзаменов"""
    exams_text = (
        "📝 <b>Расписание экзаменов</b>\n\n"
        "15 января - Математический анализ\n"
        "18 января - Программирование\n"
        "22 января - Физика\n"
    )
    
    await message.answer(
        exams_text,
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
\`\`\`

Не забудьте зарегистрировать в `main.py`:
\`\`\`python
from handlers import exams

dp.include_router(exams.router)
\`\`\`

### Отправка уведомлений всем пользователям

\`\`\`python
# handlers/admin.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from config import ADMIN_ID

router = Router()

# Список ID пользователей (в реальном проекте - из БД)
user_ids = [123456789, 987654321]

@router.message(Command("notify"))
async def cmd_notify(message: Message):
    """Отправить уведомление всем (только для админа)"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещен")
        return
    
    # Получаем текст после команды
    text = message.text.replace("/notify", "").strip()
    
    if not text:
        await message.answer("Использование: /notify <текст>")
        return
    
    # Отправляем всем
    success = 0
    for user_id in user_ids:
        try:
            await message.bot.send_message(user_id, f"📢 {text}")
            success += 1
        except Exception:
            pass
    
    await message.answer(f"✅ Отправлено {success} пользователям")
\`\`\`

### Работа с inline кнопками

\`\`\`python
# keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_schedule_keyboard():
    """Клавиатура для выбора дня недели"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Понедельник", callback_data="day_monday"),
            InlineKeyboardButton(text="Вторник", callback_data="day_tuesday"),
        ],
        [
            InlineKeyboardButton(text="Среда", callback_data="day_wednesday"),
            InlineKeyboardButton(text="Четверг", callback_data="day_thursday"),
        ],
        [
            InlineKeyboardButton(text="Пятница", callback_data="day_friday"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu"),
        ]
    ])
    return keyboard

# Обработчик callback
@router.callback_query(F.data.startswith("day_"))
async def show_day_schedule(callback: CallbackQuery):
    day = callback.data.replace("day_", "")
    # Показать расписание для выбранного дня
    await callback.message.edit_text(f"Расписание на {day}")
\`\`\`

## Примеры для Next.js приложения

### Создание новой страницы с данными

\`\`\`tsx
// app/teachers/page.tsx
import { BackButton } from '@/components/back-button'

const teachers = [
  { id: 1, name: 'Иванов И.И.', subject: 'Математика', email: 'ivanov@uni.edu' },
  { id: 2, name: 'Петров П.П.', subject: 'Программирование', email: 'petrov@uni.edu' },
]

export default function TeachersPage() {
  return (
    <main className="min-h-screen p-4 pb-8">
      <div className="max-w-2xl mx-auto">
        <BackButton />
        
        <h1 className="text-3xl font-bold mb-6">Преподаватели</h1>
        
        <div className="space-y-4">
          {teachers.map((teacher) => (
            <div key={teacher.id} className="bg-card border border-border rounded-xl p-5">
              <h3 className="font-semibold text-lg mb-1">{teacher.name}</h3>
              <p className="text-sm text-muted-foreground mb-2">{teacher.subject}</p>
              <a href={`mailto:${teacher.email}`} className="text-sm text-primary">
                {teacher.email}
              </a>
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
\`\`\`

### Создание переиспользуемого компонента

\`\`\`tsx
// components/subject-card.tsx
import { ReactNode } from 'react'

interface SubjectCardProps {
  name: string
  teacher: string
  room: string
  time: string
  icon?: ReactNode
}

export function SubjectCard({ name, teacher, room, time, icon }: SubjectCardProps) {
  return (
    <div className="bg-card border border-border rounded-xl p-4 hover:border-primary/50 transition-colors">
      <div className="flex items-start gap-3">
        {icon && (
          <div className="flex-shrink-0 rounded-lg p-2 bg-primary/10 text-primary">
            {icon}
          </div>
        )}
        
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold mb-1">{name}</h3>
          <div className="text-sm text-muted-foreground space-y-1">
            <p>👨‍🏫 {teacher}</p>
            <p>🚪 {room}</p>
            <p>🕐 {time}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Использование:
import { SubjectCard } from '@/components/subject-card'
import { BookOpen } from 'lucide-react'

<SubjectCard
  name="Программирование"
  teacher="Петров П.П."
  room="Ауд. 205"
  time="10:45 - 12:15"
  icon={<BookOpen className="w-5 h-5" />}
/>
\`\`\`

### API Route для получения данных

\`\`\`typescript
// app/api/schedule/route.ts
import { NextResponse } from 'next/server'

const scheduleData = {
  monday: [
    { time: '09:00', subject: 'Математика', room: '301' },
    { time: '10:45', subject: 'Программирование', room: '205' },
  ],
  tuesday: [
    { time: '09:00', subject: 'Физика', room: '401' },
  ],
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const day = searchParams.get('day') || 'monday'
  
  return NextResponse.json({
    day,
    classes: scheduleData[day as keyof typeof scheduleData] || []
  })
}

// Использование в компоненте:
'use client'
import { useEffect, useState } from 'react'

export function ScheduleList() {
  const [schedule, setSchedule] = useState([])
  
  useEffect(() => {
    fetch('/api/schedule?day=monday')
      .then(res => res.json())
      .then(data => setSchedule(data.classes))
  }, [])
  
  return (
    <div>
      {schedule.map((item, i) => (
        <div key={i}>{item.subject}</div>
      ))}
    </div>
  )
}
\`\`\`

### Использование Telegram Web App API

\`\`\`typescript
// lib/telegram-utils.ts
import { telegram } from './telegram'

// Показать главную кнопку
export function showMainButton(text: string, onClick: () => void) {
  if (telegram) {
    telegram.MainButton.text = text
    telegram.MainButton.show()
    telegram.MainButton.onClick(onClick)
  }
}

// Скрыть главную кнопку
export function hideMainButton() {
  if (telegram) {
    telegram.MainButton.hide()
  }
}

// Закрыть приложение
export function closeApp() {
  if (telegram) {
    telegram.close()
  }
}

// Показать кнопку "Назад"
export function showBackButton(onClick: () => void) {
  if (telegram) {
    telegram.BackButton.show()
    telegram.BackButton.onClick(onClick)
  }
}

// Использование в компоненте:
'use client'
import { useEffect } from 'react'
import { showMainButton, hideMainButton } from '@/lib/telegram-utils'

export function SubmitForm() {
  useEffect(() => {
    showMainButton('Отправить', () => {
      // Обработка отправки
      console.log('Форма отправлена')
    })
    
    return () => hideMainButton()
  }, [])
  
  return <form>{/* Поля формы */}</form>
}
\`\`\`

### Интеграция с Supabase

\`\`\`typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseKey)

// Получение расписания из БД
export async function getSchedule(day: string) {
  const { data, error } = await supabase
    .from('schedule')
    .select('*')
    .eq('day', day)
    .order('time')
  
  if (error) throw error
  return data
}

// Добавление домашнего задания
export async function addHomework(homework: {
  subject: string
  title: string
  description: string
  deadline: string
}) {
  const { data, error } = await supabase
    .from('homework')
    .insert([homework])
  
  if (error) throw error
  return data
}

// Использование в компоненте:
'use client'
import { useEffect, useState } from 'react'
import { getSchedule } from '@/lib/supabase'

export function ScheduleFromDB() {
  const [schedule, setSchedule] = useState([])
  
  useEffect(() => {
    getSchedule('monday').then(setSchedule)
  }, [])
  
  return (
    <div>
      {schedule.map((item: any) => (
        <div key={item.id}>{item.subject}</div>
      ))}
    </div>
  )
}
\`\`\`

## Полезные сниппеты

### Форматирование даты на русском

\`\`\`typescript
export function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}

// Использование:
formatDate('2025-10-05') // "5 октября 2025 г."
\`\`\`

### Проверка дедлайна

\`\`\`typescript
export function isDeadlineSoon(deadline: string, daysThreshold = 3) {
  const deadlineDate = new Date(deadline)
  const today = new Date()
  const diffTime = deadlineDate.getTime() - today.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  return diffDays <= daysThreshold && diffDays >= 0
}

// Использование:
if (isDeadlineSoon(homework.deadline)) {
  // Показать предупреждение
}
\`\`\`

### Сортировка по приоритету

\`\`\`typescript
const priorityOrder = { high: 0, medium: 1, low: 2 }

const sortedHomework = homework.sort((a, b) => 
  priorityOrder[a.priority] - priorityOrder[b.priority]
)
