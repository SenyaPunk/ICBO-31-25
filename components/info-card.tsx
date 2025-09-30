import type { ReactNode } from "react"
import { ExternalLink } from "lucide-react"

interface InfoCardProps {
  icon: ReactNode
  title: string
  description: string
  link?: string
}

export function InfoCard({ icon, title, description, link }: InfoCardProps) {
  const content = (
    <div className="bg-card border border-border rounded-xl p-4 hover:border-primary/50 transition-colors">
      <div className="flex items-center gap-4">
        <div className="flex-shrink-0 rounded-lg p-2 bg-primary/10 text-primary">{icon}</div>

        <div className="flex-1 min-w-0">
          <h3 className="font-semibold mb-1 text-balance">{title}</h3>
          <p className="text-sm text-muted-foreground text-balance">{description}</p>
        </div>

        {link && <ExternalLink className="w-4 h-4 text-muted-foreground flex-shrink-0" />}
      </div>
    </div>
  )

  if (link) {
    return (
      <a href={link} target="_blank" rel="noopener noreferrer">
        {content}
      </a>
    )
  }

  return content
}
