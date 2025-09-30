"use client"

import type React from "react"

import { useEffect } from "react"
import { initTelegramApp } from "@/lib/telegram"

export function TelegramProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    initTelegramApp()
  }, [])

  return <>{children}</>
}
