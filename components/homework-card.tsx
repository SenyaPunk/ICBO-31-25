import { Clock, AlertCircle } from "lucide-react"

interface HomeworkCardProps {
  subject: string
  title: string
  description: string
  deadline: string
  priority: "high" | "medium" | "low"
}

export function HomeworkCard({ subject, title, description, deadline, priority }: HomeworkCardProps) {
  const priorityColors = {
    high: "text-red-500 bg-red-500/10",
    medium: "text-primary bg-primary/10",
    low: "text-green-500 bg-green-500/10",
  }

  const priorityLabels = {
    high: "Высокий приоритет",
    medium: "Средний приоритет",
    low: "Низкий приоритет",
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("ru-RU", { day: "numeric", month: "long" })
  }

  return (
    <div className="bg-card border border-border rounded-xl p-5 hover:border-primary/50 transition-colors">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-primary mb-1">{subject}</div>
          <h3 className="font-semibold text-lg text-balance">{title}</h3>
        </div>

        {priority === "high" && <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />}
      </div>

      <p className="text-muted-foreground text-sm mb-4 text-balance">{description}</p>

      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="w-4 h-4" />
          <span>Дедлайн: {formatDate(deadline)}</span>
        </div>

        <div className={`text-xs font-medium px-3 py-1 rounded-full ${priorityColors[priority]}`}>
          {priorityLabels[priority]}
        </div>
      </div>
    </div>
  )
}
