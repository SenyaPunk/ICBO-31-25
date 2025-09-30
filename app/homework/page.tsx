import { BackButton } from "@/components/back-button"
import { HomeworkCard } from "@/components/homework-card"

const homeworkData = [
  {
    id: 1,
    subject: "Программирование",
    title: "Лабораторная работа №3",
    description: "Реализовать алгоритм сортировки слиянием",
    deadline: "2025-10-05",
    priority: "high" as const,
  },
  {
    id: 2,
    subject: "Математический анализ",
    title: "Домашнее задание",
    description: "Решить задачи 15-20 из учебника",
    deadline: "2025-10-07",
    priority: "medium" as const,
  },
  {
    id: 3,
    subject: "Английский язык",
    title: "Эссе",
    description: 'Написать эссе на тему "Technology in modern life"',
    deadline: "2025-10-10",
    priority: "low" as const,
  },
  {
    id: 4,
    subject: "Базы данных",
    title: "Проектирование БД",
    description: "Создать ER-диаграмму для системы управления библиотекой",
    deadline: "2025-10-08",
    priority: "high" as const,
  },
]

export default function HomeworkPage() {
  return (
    <main className="min-h-screen p-4 pb-8">
      <div className="max-w-2xl mx-auto">
        <BackButton />

        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2 text-balance">Домашние задания</h1>
          <p className="text-muted-foreground">Актуальные задания с дедлайнами</p>
        </div>

        <div className="space-y-4">
          {homeworkData.map((homework) => (
            <HomeworkCard key={homework.id} {...homework} />
          ))}
        </div>
      </div>
    </main>
  )
}
