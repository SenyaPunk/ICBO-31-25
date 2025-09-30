interface ClassInfo {
  time: string
  subject: string
  room: string
  teacher: string
}

interface DayScheduleProps {
  day: string
  classes: ClassInfo[]
}

export function DaySchedule({ day, classes }: DayScheduleProps) {
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
                <h3 className="font-semibold mb-1 text-balance">{classInfo.subject}</h3>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
                  <span>{classInfo.room}</span>
                  <span>•</span>
                  <span>{classInfo.teacher}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
