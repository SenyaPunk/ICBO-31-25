import { BackButton } from "@/components/back-button"
import { NotificationCard } from "@/components/notification-card"

const notifications = [
  {
    id: 1,
    title: "Изменение в расписании",
    message: "Завтра занятие по программированию перенесено на 14:00",
    date: "2025-10-01",
    type: "warning" as const,
  },
  {
    id: 2,
    title: "Новое домашнее задание",
    message: "Добавлено задание по базам данных, дедлайн 8 октября",
    date: "2025-09-30",
    type: "info" as const,
  },
  {
    id: 3,
    title: "Собрание группы",
    message: "В пятницу в 15:00 состоится собрание группы в ауд. 301",
    date: "2025-09-29",
    type: "info" as const,
  },
]

export default function NotificationsPage() {
  return (
    <main className="min-h-screen p-4 pb-8">
      <div className="max-w-2xl mx-auto">
        <BackButton />

        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2 text-balance">Уведомления</h1>
          <p className="text-muted-foreground">Важные объявления и новости</p>
        </div>

        <div className="space-y-4">
          {notifications.map((notification) => (
            <NotificationCard key={notification.id} {...notification} />
          ))}
        </div>
      </div>
    </main>
  )
}
