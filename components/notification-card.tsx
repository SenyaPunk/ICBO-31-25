import { Bell, AlertTriangle } from "lucide-react"

interface NotificationCardProps {
  title: string
  message: string
  date: string
  type: "info" | "warning"
}

export function NotificationCard({ title, message, date, type }: NotificationCardProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("ru-RU", { day: "numeric", month: "long" })
  }

  return (
    <div className="bg-card border border-border rounded-xl p-5 hover:border-primary/50 transition-colors">
      <div className="flex items-start gap-4">
        <div
          className={`
          flex-shrink-0 rounded-lg p-2
          ${type === "warning" ? "bg-red-500/10 text-red-500" : "bg-primary/10 text-primary"}
        `}
        >
          {type === "warning" ? <AlertTriangle className="w-5 h-5" /> : <Bell className="w-5 h-5" />}
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="font-semibold mb-1 text-balance">{title}</h3>
          <p className="text-sm text-muted-foreground mb-2 text-balance">{message}</p>
          <div className="text-xs text-muted-foreground">{formatDate(date)}</div>
        </div>
      </div>
    </div>
  )
}
