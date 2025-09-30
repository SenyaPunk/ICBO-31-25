import { BackButton } from "@/components/back-button"
import { DaySchedule } from "@/components/day-schedule"

const scheduleData = [
  {
    day: "Понедельник",
    classes: [
      { time: "09:00 - 10:30", subject: "Математический анализ", room: "Ауд. 301", teacher: "Иванов И.И." },
      { time: "10:45 - 12:15", subject: "Программирование", room: "Ауд. 205", teacher: "Петров П.П." },
      { time: "13:00 - 14:30", subject: "Английский язык", room: "Ауд. 112", teacher: "Сидорова С.С." },
    ],
  },
  {
    day: "Вторник",
    classes: [
      { time: "09:00 - 10:30", subject: "Физика", room: "Ауд. 401", teacher: "Козлов К.К." },
      { time: "10:45 - 12:15", subject: "Алгоритмы и структуры данных", room: "Ауд. 205", teacher: "Петров П.П." },
    ],
  },
  {
    day: "Среда",
    classes: [
      { time: "09:00 - 10:30", subject: "Базы данных", room: "Ауд. 210", teacher: "Новиков Н.Н." },
      { time: "10:45 - 12:15", subject: "Дискретная математика", room: "Ауд. 305", teacher: "Иванов И.И." },
      { time: "13:00 - 14:30", subject: "Физическая культура", room: "Спортзал", teacher: "Смирнов С.С." },
    ],
  },
]

export default function SchedulePage() {
  return (
    <main className="min-h-screen p-4 pb-8">
      <div className="max-w-2xl mx-auto">
        <BackButton />

        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2 text-balance">Расписание занятий</h1>
          <p className="text-muted-foreground">Актуальное расписание на текущую неделю</p>
        </div>

        <div className="space-y-6">
          {scheduleData.map((day) => (
            <DaySchedule key={day.day} day={day.day} classes={day.classes} />
          ))}
        </div>
      </div>
    </main>
  )
}
