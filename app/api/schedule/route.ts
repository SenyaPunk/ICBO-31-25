import { NextResponse } from "next/server"

// Типы для расписания
interface Lesson {
  time: string
  subject: string
  room: string
  teacher: string
  type?: string
}

interface WeekSchedule {
  [key: string]: Lesson[]
}

// Моковые данные расписания для группы ИКБО-31-25
const mockSchedule: WeekSchedule = {
  понедельник: [
    {
      time: "09:00-10:30",
      subject: "Математический анализ",
      room: "Ауд. 301",
      teacher: "Иванов И.И.",
      type: "Лекция",
    },
    {
      time: "10:45-12:15",
      subject: "Программирование",
      room: "Ауд. 205",
      teacher: "Петров П.П.",
      type: "Практика",
    },
    {
      time: "12:30-14:00",
      subject: "Английский язык",
      room: "Ауд. 410",
      teacher: "Смирнова А.А.",
      type: "Практика",
    },
  ],
  вторник: [
    {
      time: "09:00-10:30",
      subject: "Базы данных",
      room: "Ауд. 302",
      teacher: "Козлов К.К.",
      type: "Лекция",
    },
    {
      time: "10:45-12:15",
      subject: "Базы данных",
      room: "Ауд. 206",
      teacher: "Козлов К.К.",
      type: "Лабораторная",
    },
    {
      time: "12:30-14:00",
      subject: "Физическая культура",
      room: "Спортзал",
      teacher: "Волков В.В.",
      type: "Практика",
    },
  ],
  среда: [
    {
      time: "09:00-10:30",
      subject: "Алгоритмы и структуры данных",
      room: "Ауд. 301",
      teacher: "Новиков Н.Н.",
      type: "Лекция",
    },
    {
      time: "10:45-12:15",
      subject: "Алгоритмы и структуры данных",
      room: "Ауд. 205",
      teacher: "Новиков Н.Н.",
      type: "Практика",
    },
    {
      time: "12:30-14:00",
      subject: "Веб-разработка",
      room: "Ауд. 207",
      teacher: "Сидоров С.С.",
      type: "Лабораторная",
    },
  ],
  четверг: [
    {
      time: "09:00-10:30",
      subject: "Операционные системы",
      room: "Ауд. 303",
      teacher: "Морозов М.М.",
      type: "Лекция",
    },
    {
      time: "10:45-12:15",
      subject: "Операционные системы",
      room: "Ауд. 208",
      teacher: "Морозов М.М.",
      type: "Лабораторная",
    },
    {
      time: "13:00-14:30",
      subject: "Дискретная математика",
      room: "Ауд. 305",
      teacher: "Иванов И.И.",
      type: "Практика",
    },
  ],
  пятница: [
    {
      time: "09:00-10:30",
      subject: "Математический анализ",
      room: "Ауд. 301",
      teacher: "Иванов И.И.",
      type: "Практика",
    },
    {
      time: "10:45-12:15",
      subject: "Программирование",
      room: "Ауд. 205",
      teacher: "Петров П.П.",
      type: "Лабораторная",
    },
    {
      time: "12:30-14:00",
      subject: "Философия",
      room: "Ауд. 501",
      teacher: "Федорова Ф.Ф.",
      type: "Лекция",
    },
  ],
  суббота: [],
}

export async function GET() {
  try {
    // В будущем здесь можно добавить реальный парсинг с сайта
    // Пока возвращаем моковые данные
    return NextResponse.json({
      success: true,
      group: "ИКБО-31-25",
      schedule: mockSchedule,
    })
  } catch (error) {
    console.error("[v0] Error fetching schedule:", error)
    return NextResponse.json({ success: false, error: "Failed to fetch schedule" }, { status: 500 })
  }
}
