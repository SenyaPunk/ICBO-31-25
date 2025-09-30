"use client"

import { ArrowLeft } from "lucide-react"
import { useRouter } from "next/navigation"

export function BackButton() {
  const router = useRouter()

  return (
    <button
      onClick={() => router.back()}
      className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors mb-6 -ml-2 p-2 rounded-lg hover:bg-muted/50"
    >
      <ArrowLeft className="w-5 h-5" />
      <span className="font-medium">Назад</span>
    </button>
  )
}
