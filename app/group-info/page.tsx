import { BackButton } from "@/components/back-button"
import { InfoCard } from "@/components/info-card"
import { Users, Mail, MessageCircle, ExternalLink } from "lucide-react"

export default function GroupInfoPage() {
  return (
    <main className="min-h-screen p-4 pb-8">
      <div className="max-w-2xl mx-auto">
        <BackButton />

        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2 text-balance">Информация о группе</h1>
          <p className="text-muted-foreground">Контакты, ссылки и полезная информация</p>
        </div>

        <div className="space-y-6">
          {/* Group Info */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4">Группа ИВТ-301</h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Курс:</span>
                <span className="font-medium">3 курс</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Факультет:</span>
                <span className="font-medium">Информационные технологии</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Студентов:</span>
                <span className="font-medium">25 человек</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Куратор:</span>
                <span className="font-medium">Иванова М.А.</span>
              </div>
            </div>
          </div>

          {/* Contacts */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Контакты</h2>
            <div className="space-y-3">
              <InfoCard
                icon={<Users className="w-5 h-5" />}
                title="Староста группы"
                description="Алексей Петров"
                link="https://t.me/username"
              />
              <InfoCard
                icon={<Mail className="w-5 h-5" />}
                title="Email группы"
                description="ivt301@university.edu"
                link="mailto:ivt301@university.edu"
              />
              <InfoCard
                icon={<MessageCircle className="w-5 h-5" />}
                title="Чат группы"
                description="Общий чат в Telegram"
                link="https://t.me/ivt301chat"
              />
            </div>
          </div>

          {/* Useful Links */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Полезные ссылки</h2>
            <div className="space-y-3">
              <InfoCard
                icon={<ExternalLink className="w-5 h-5" />}
                title="Электронная библиотека"
                description="Доступ к учебным материалам"
                link="https://library.university.edu"
              />
              <InfoCard
                icon={<ExternalLink className="w-5 h-5" />}
                title="Личный кабинет"
                description="Система управления обучением"
                link="https://lms.university.edu"
              />
              <InfoCard
                icon={<ExternalLink className="w-5 h-5" />}
                title="Google Drive группы"
                description="Общие документы и материалы"
                link="https://drive.google.com"
              />
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
