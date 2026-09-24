import { motion } from 'framer-motion'
import { InterviewerStatus } from '../../types/interviewRoom'

interface AIInterviewerProps {
  status: InterviewerStatus
  micLevel: number
  name?: string
}

const STATUS_CONFIG: Record<
  InterviewerStatus,
  { label: string; accent: 'ready' | 'active' | 'warn' | 'recording' }
> = {
  idle: { label: 'Ready', accent: 'ready' },
  thinking: { label: 'Thinking...', accent: 'active' },
  speaking: { label: 'Speaking', accent: 'active' },
  listening: { label: 'Listening', accent: 'recording' },
  evaluating: { label: 'Evaluating response...', accent: 'active' },
  nextQuestion: { label: 'Preparing next question...', accent: 'active' },
}

function accentClasses(accent: STATUS_CONFIG_ACCENT) {
  switch (accent) {
    case 'ready':
      return 'text-accent border-accent/40 bg-accent/10'
    case 'active':
      return 'text-primary border-primary/40 bg-primary/10'
    case 'recording':
      return 'text-error border-error/40 bg-error/10'
    case 'warn':
      return 'text-warning border-warning/40 bg-warning/10'
  }
}

type STATUS_CONFIG_ACCENT = 'ready' | 'active' | 'warn' | 'recording'

export function AIInterviewer({
  status,
  micLevel,
  name = 'AI Interviewer',
}: AIInterviewerProps) {
  const cfg = STATUS_CONFIG[status]

  return (
    <div
      className={`relative w-full overflow-hidden rounded-xl border bg-background flex items-center justify-center transition-shadow duration-500 ${
        status === 'speaking'
          ? 'border-primary/50 animate-speak-glow'
          : 'border-surface-light'
      }`}
      style={{
        aspectRatio: '4 / 3',
        minHeight: '420px',
        maxHeight: '480px',
        height: '460px',
      }}
    >
      {/* Neutral professional backdrop */}
      <div
        className="absolute inset-0"
        style={{
          background:
            'radial-gradient(120% 120% at 50% 110%, #1e3a5f 0%, #0f2440 45%, #0b1b30 100%)',
        }}
      />
      <div
        className="absolute inset-0 opacity-40"
        style={{
          background:
            'linear-gradient(180deg, rgba(255,255,255,0.05) 0%, transparent 30%, transparent 80%, rgba(0,0,0,0.35) 100%)',
        }}
      />

      {/* Real interviewer image — static, no facial animation */}
      <img
        src="/assets/images/avatar.jpeg"
        alt="AI Interviewer"
        className="absolute inset-0 z-10 h-full w-full object-cover object-center"
        style={{ objectPosition: 'center 25%' }}
        draggable={false}
      />

      {/* Bottom scrim so the status caption stays readable */}
      <div
        className="absolute inset-x-0 bottom-0 z-10 h-24"
        style={{
          background:
            'linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.55) 100%)',
        }}
      />

      {/* Audio waveform while TTS is speaking — communicates audio activity, not face animation */}
      {status === 'speaking' && (
        <div className="absolute inset-x-0 bottom-14 z-20 flex items-end justify-center gap-1">
          {[0.45, 0.75, 0.55, 0.95, 0.6, 0.85, 0.4, 0.7, 0.5].map((h, i) => (
            <span
              key={i}
              className="animate-wave-bar w-1 rounded-full bg-primary/90 shadow-[0_0_6px_rgba(56,189,248,0.6)]"
              style={{
                height: `${16 + h * 26 + micLevel * 10}px`,
                animationDelay: `${i * 0.09}s`,
              }}
            />
          ))}
        </div>
      )}

      {/* LIVE badge */}
      <div className="absolute left-3 top-3 z-20 flex items-center gap-1.5 rounded-full bg-background/80 border border-surface-light px-2.5 py-1">
        <span className="relative flex h-2 w-2">
          <span className="animate-dot-ping absolute inline-flex h-full w-full rounded-full bg-error opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-error" />
        </span>
        <span className="text-[11px] font-semibold uppercase tracking-wider text-text">Live</span>
      </div>

      {/* State indicator */}
      <div className="absolute bottom-3 left-1/2 z-20 -translate-x-1/2">
        <div
          className={`flex items-center gap-2 rounded-full border px-3 py-1.5 backdrop-blur-sm ${accentClasses(
            cfg.accent
          )}`}
        >
          <StateGlyph status={status} micLevel={micLevel} />
          <span className="text-xs font-medium">{cfg.label}</span>
        </div>
      </div>

      {/* Name caption */}
      <div className="absolute bottom-3 right-3 z-20 hidden sm:block">
        <span className="text-[11px] font-medium text-text-secondary/80">{name}</span>
      </div>
    </div>
  )
}

function StateGlyph({
  status,
  micLevel,
}: {
  status: InterviewerStatus
  micLevel: number
}) {
  if (status === 'speaking') {
    return <WaveformBars level={micLevel} />
  }
  if (status === 'listening') {
    return (
      <span className="flex h-2 w-2 rounded-full bg-current animate-mic-pulse" />
    )
  }
  if (status === 'thinking' || status === 'evaluating' || status === 'nextQuestion') {
    return <ThinkingDots />
  }
  return <span className="h-2 w-2 rounded-full bg-accent" />
}

function WaveformBars({ level }: { level: number }) {
  const heights = [0.5, 0.9, 0.35, 0.75, 0.5, 0.85, 0.4]
  return (
    <span className="flex items-end gap-[3px] h-3.5">
      {heights.map((h, i) => (
        <span
          key={i}
          className="animate-wave-bar w-[3px] rounded-full bg-current"
          style={{
            height: `${Math.min(100, (h + level * 0.3) * 100)}%`,
            animationDelay: `${i * 0.09}s`,
            transformOrigin: 'center',
          }}
        />
      ))}
    </span>
  )
}

function ThinkingDots() {
  return (
    <span className="flex items-center gap-1">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-current"
          animate={{ opacity: [0.3, 1, 0.3], y: [0, -3, 0] }}
          transition={{ duration: 1.1, repeat: Infinity, delay: i * 0.2 }}
        />
      ))}
    </span>
  )
}
