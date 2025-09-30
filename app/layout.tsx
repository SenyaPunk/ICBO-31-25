import type React from "react"
import { GeistSans } from "geist/font/sans"
import "./globals.css"
import { TelegramProvider } from "./telegram-provider"

export const metadata = {
  title: "Университетская группа",
  description: "Приложение для управления университетской группой",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ru" className={`${GeistSans.variable} antialiased dark`}>
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
