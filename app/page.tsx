import { MenuCard } from "@/components/menu-card"
import { Calendar, BookOpen, Users, Bell } from "lucide-react"

export default function HomePage() {
  return (
    <main className="min-h-screen p-4 pb-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8 pt-4">
          <h1 className="text-3xl font-bold mb-2 text-balance">Университетская группа</h1>
          <p className="text-muted-foreground text-balance">
            Управляйте расписанием, домашними заданиями и информацией о группе
          </p>
        </div>

        {/* Menu Grid */}
        <div className="grid grid-cols-1 gap-4">
          <MenuCard
            href="/schedule"
            icon={<Calendar className="w-6 h-6" />}
            title="Расписание"
            description="Просмотр расписания занятий на неделю"
            color="primary"
          />

          <MenuCard
            href="/homework"
            icon={<BookOpen className="w-6 h-6" />}
            title="Домашние задания"
            description="Список актуальных заданий с дедлайнами"
            color="secondary"
          />

          <MenuCard
            href="/group-info"
            icon={<Users className="w-6 h-6" />}
            title="Информация о группе"
            description="Контакты, ссылки и полезная информация"
            color="secondary"
          />

          <MenuCard
            href="/notifications"
            icon={<Bell className="w-6 h-6" />}
            title="Уведомления"
            description="Важные объявления и новости"
            color="secondary"
          />
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-muted-foreground">
          <p>Telegram Mini App для студентов</p>
        </div>
      </div>
    </main>
  )
}
