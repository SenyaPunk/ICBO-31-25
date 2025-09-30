import type React from "react"
import { Geist } from "next/font/google"
import "./globals.css"
import { TelegramProvider } from "./telegram-provider"

const geistSans = Geist({
  subsets: ["latin", "cyrillic"],
  variable: "--font-geist-sans",
})

export const metadata = {
  title: "Университетская группа",
  description: "Приложение для управления университетской группой",
    generator: 'v0.app'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ru" className={`${geistSans.variable} antialiased dark`}>
      <head>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
      </head>
      <body className="font-sans bg-background text-foreground">
        <TelegramProvider>{children}</TelegramProvider>
      </body>
    </html>
  )
}
