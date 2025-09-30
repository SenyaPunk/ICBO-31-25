interface ClassInfo {
  time: string
  subject: string
  room: string
  teacher: string
  type?: string
}

interface DayScheduleProps {
  day: string
  classes: ClassInfo[]
}

const getLessonEmoji = (type?: string) => {
  const emojiMap: Record<string, string> = {
    Лекция: "📚",
    Практика: "✏️",
    Лабораторная: "🔬",
  }
  return type ? emojiMap[type] || "📖" : "📖"
}

export function DaySchedule({ day, classes }: DayScheduleProps) {
  if (classes.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        <div className="bg-primary/10 border-b border-border px-4 py-3">
          <h2 className="font-semibold text-lg text-primary">{day}</h2>
        </div>
        <div className="p-8 text-center text-muted-foreground">
          <p className="text-2xl mb-2">🎉</p>
          <p>Нет занятий</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      <div className="bg-primary/10 border-b border-border px-4 py-3">
        <h2 className="font-semibold text-lg text-primary">{day}</h2>
      </div>

      <div className="divide-y divide-border">
        {classes.map((classInfo, index) => (
          <div key={index} className="p-4 hover:bg-muted/50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 text-sm font-medium text-muted-foreground min-w-[100px]">
                {classInfo.time}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">{getLessonEmoji(classInfo.type)}</span>
                  <h3 className="font-semibold text-balance">{classInfo.subject}</h3>
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
                  <span>👨‍🏫 {classInfo.teacher}</span>
                  <span>•</span>
                  <span>🚪 {classInfo.room}</span>
                  {classInfo.type && (
                    <>
                      <span>•</span>
                      <span>{classInfo.type}</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
