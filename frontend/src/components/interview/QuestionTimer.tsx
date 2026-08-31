import { useEffect, useRef, useState } from 'react'
import { Clock3, AlertTriangle } from 'lucide-react'

interface QuestionTimerProps {
  questionKey: string
  timeLimitSeconds?: number
  onTimeUpdate?: (data: {
    elapsedSeconds: number
    remainingSeconds: number
    overtimeSeconds: number
    isOvertime: boolean
  }) => void
}

export function QuestionTimer({
  questionKey,
  timeLimitSeconds = 60,
  onTimeUpdate,
}: QuestionTimerProps) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const startedAtRef = useRef<number>(Date.now())
  const callbackRef = useRef(onTimeUpdate)

  useEffect(() => {
    callbackRef.current = onTimeUpdate
  }, [onTimeUpdate])

  useEffect(() => {
    startedAtRef.current = Date.now()
    setElapsedSeconds(0)

    const updateTimer = () => {
      const elapsed = Math.floor(
        (Date.now() - startedAtRef.current) / 1000
      )

      const remaining = Math.max(
        0,
        timeLimitSeconds - elapsed
      )

      const overtime = Math.max(
        0,
        elapsed - timeLimitSeconds
      )

      setElapsedSeconds(elapsed)

      callbackRef.current?.({
        elapsedSeconds: elapsed,
        remainingSeconds: remaining,
        overtimeSeconds: overtime,
        isOvertime: overtime > 0,
      })
    }

    updateTimer()

    const interval = window.setInterval(updateTimer, 1000)

    return () => window.clearInterval(interval)
  }, [questionKey, timeLimitSeconds])

  const remainingSeconds = Math.max(
    0,
    timeLimitSeconds - elapsedSeconds
  )

  const overtimeSeconds = Math.max(
    0,
    elapsedSeconds - timeLimitSeconds
  )

  const isOvertime = overtimeSeconds > 0
  const isWarning = !isOvertime && remainingSeconds <= 10

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60

    return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }

  return (
    <div
      className={[
        'flex items-center gap-4 rounded-xl border px-5 py-3',
        'min-w-[270px] transition-all duration-300',
        isOvertime
          ? 'border-red-500/70 bg-red-500/10'
          : isWarning
            ? 'border-yellow-500/70 bg-yellow-500/10'
            : 'border-slate-600 bg-slate-800/80',
      ].join(' ')}
    >
      <div
        className={[
          'flex h-12 w-12 items-center justify-center rounded-full',
          isOvertime
            ? 'bg-red-500/20 text-red-400'
            : isWarning
              ? 'bg-yellow-500/20 text-yellow-400'
              : 'bg-cyan-500/20 text-cyan-400',
        ].join(' ')}
      >
        {isOvertime ? (
          <AlertTriangle size={25} />
        ) : (
          <Clock3 size={25} />
        )}
      </div>

      <div>
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          {isOvertime ? 'OVERTIME' : 'TIME REMAINING'}
        </div>

        <div
          className={[
            'font-mono text-3xl font-bold tracking-widest',
            isOvertime
              ? 'text-red-400'
              : isWarning
                ? 'text-yellow-400'
                : 'text-white',
          ].join(' ')}
        >
          {isOvertime
            ? `+${formatTime(overtimeSeconds)}`
            : formatTime(remainingSeconds)}
        </div>

        <div
          className={[
            'text-xs font-medium',
            isOvertime
              ? 'text-red-300'
              : isWarning
                ? 'text-yellow-300'
                : 'text-slate-500',
          ].join(' ')}
        >
          {isOvertime
            ? 'Time exceeded — penalty applies'
            : isWarning
              ? 'Less than 10 seconds'
              : '60 seconds per question'}
        </div>
      </div>
    </div>
  )
}
