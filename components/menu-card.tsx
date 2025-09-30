import Link from "next/link"
import type { ReactNode } from "react"
import { ChevronRight } from "lucide-react"

interface MenuCardProps {
  href: string
  icon: ReactNode
  title: string
  description: string
  color?: "primary" | "secondary"
}

export function MenuCard({ href, icon, title, description, color = "secondary" }: MenuCardProps) {
  const isPrimary = color === "primary"

  return (
    <Link href={href}>
      <div
        className={`
        group relative overflow-hidden rounded-xl p-6 
        transition-all duration-200 active:scale-[0.98]
        ${isPrimary ? "bg-primary text-primary-foreground" : "bg-card border border-border hover:border-primary/50"}
      `}
      >
        <div className="flex items-start gap-4">
          <div
            className={`
            flex-shrink-0 rounded-lg p-3
            ${isPrimary ? "bg-black/10" : "bg-primary/10 text-primary"}
          `}
          >
            {icon}
          </div>

          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold mb-1 text-balance">{title}</h3>
            <p
              className={`
              text-sm text-balance
              ${isPrimary ? "text-primary-foreground/80" : "text-muted-foreground"}
            `}
            >
              {description}
            </p>
          </div>

          <ChevronRight
            className={`
            flex-shrink-0 w-5 h-5 transition-transform group-hover:translate-x-1
            ${isPrimary ? "text-primary-foreground/60" : "text-muted-foreground"}
          `}
          />
        </div>
      </div>
    </Link>
  )
}
