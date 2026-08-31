import { useEffect, useState } from 'react'
import { Clock3 } from 'lucide-react'

interface InterviewDurationProps {
  startTime: number
}

export function QuestionTimer({ startTime }: InterviewDurationProps) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const update = () => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000))
    }

    update()
    const interval = window.setInterval(update, 1000)

    return () => window.clearInterval(interval)
  }, [startTime])

  const minutes = Math.floor(elapsed / 60)
  const seconds = elapsed % 60
  const formatted = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`

  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-600 bg-slate-800/80 px-5 py-3 min-w-[220px]">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-cyan-500/20 text-cyan-400">
        <Clock3 size={22} />
      </div>

      <div>
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Interview Duration
        </div>
        <div className="font-mono text-2xl font-bold tracking-widest text-white">
          {formatted}
        </div>
      </div>
    </div>
  )
}
