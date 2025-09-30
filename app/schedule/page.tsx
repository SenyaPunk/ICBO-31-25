"use client"

import { BackButton } from "@/components/back-button"
import { DaySchedule } from "@/components/day-schedule"
import { useEffect, useState } from "react"

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

interface ScheduleData {
  day: string
  classes: Lesson[]
}

export default function SchedulePage() {
  const [scheduleData, setScheduleData] = useState<ScheduleData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchSchedule() {
      try {
        const response = await fetch("/api/schedule")
        const data = await response.json()

        if (data.success) {
          // Преобразуем данные в нужный формат
          const dayNames: Record<string, string> = {
            понедельник: "Понедельник",
            вторник: "Вторник",
            среда: "Среда",
            четверг: "Четверг",
            пятница: "Пятница",
            суббота: "Суббота",
          }

          const formatted: ScheduleData[] = Object.entries(data.schedule as WeekSchedule).map(([day, classes]) => ({
            day: dayNames[day] || day,
            classes: classes as Lesson[],
          }))

          setScheduleData(formatted)
        } else {
          setError("Не удалось загрузить расписание")
        }
      } catch (err) {
        console.error("[v0] Error loading schedule:", err)
        setError("Ошибка при загрузке расписания")
      } finally {
        setLoading(false)
      }
    }

    fetchSchedule()
  }, [])

  return (
    <main className="min-h-screen p-4 pb-8">
      <div className="max-w-2xl mx-auto">
        <BackButton />

        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2 text-balance">Расписание занятий</h1>
          <p className="text-muted-foreground">Группа ИКБО-31-25 • Текущая неделя</p>
        </div>

        {loading ? (
          <div className="space-y-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-card border border-border rounded-xl p-4 animate-pulse">
                <div className="h-6 bg-muted rounded w-32 mb-4"></div>
                <div className="space-y-3">
                  <div className="h-4 bg-muted rounded"></div>
                  <div className="h-4 bg-muted rounded w-3/4"></div>
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="bg-destructive/10 border border-destructive/20 rounded-xl p-6 text-center">
            <p className="text-destructive font-medium">{error}</p>
          </div>
        ) : (
          <div className="space-y-6">
            {scheduleData.map((day) => (
              <DaySchedule key={day.day} day={day.day} classes={day.classes} />
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
