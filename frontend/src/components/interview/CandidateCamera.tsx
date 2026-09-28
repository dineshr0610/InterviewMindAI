import { useRef } from 'react'
import { cn } from '../../utils/cn'
import { User, VideoOff, Mic, MicOff } from 'lucide-react'

interface CandidateCameraProps {
  isActive: boolean
  microphoneActive: boolean
  setVideoElement: (el: HTMLVideoElement | null) => void
  className?: string
}

export function CandidateCamera({
  isActive,
  microphoneActive,
  setVideoElement,
  className,
}: CandidateCameraProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null)

  const bindRef = (el: HTMLVideoElement | null) => {
    videoRef.current = el
    setVideoElement(el)
  }

  return (
    <div
      className={cn(
        'relative aspect-[4/3] w-full overflow-hidden rounded-lg border border-surface-light bg-background',
        isActive ? '' : 'bg-black/60',
        className
      )}
    >
      {/*
        The self-view shows the candidate's VIDEO ONLY. It is permanently
        muted so the microphone is never routed to the speakers (which would
        cause the candidate to hear their own voice). The microphone audio
        is used exclusively for recording / level analysis / transcription.
      */}
      <video
        ref={bindRef}
        autoPlay
        muted
        playsInline
        className={cn(
          'h-full w-full object-cover transition-opacity duration-300',
          isActive ? 'opacity-100 -scale-x-100' : 'opacity-0'
        )}
      />

      {/* Fallback when camera is off/unavailable */}
      {!isActive && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-1.5 text-text-secondary">
          <VideoOff className="h-5 w-5" />
          <span className="text-[11px] font-medium">Camera Off</span>
        </div>
      )}

      {/* Camera placeholder icon always visible on top for identity */}
      <div className="pointer-events-none absolute left-2.5 top-2.5 flex items-center gap-1.5">
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-background/70 text-primary">
          <User className="h-3 w-3" />
        </span>
        <span className="text-[10px] font-semibold uppercase tracking-wider text-text/80">
          You
        </span>
      </div>

      {/* Mic + camera status line */}
      <div className="pointer-events-none absolute bottom-1.5 left-1.5 right-1.5 flex items-center justify-between gap-1">
        <span
          className={cn(
            'inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[9px] font-medium',
            microphoneActive ? 'bg-accent/20 text-accent' : 'bg-error/20 text-error'
          )}
        >
          {microphoneActive ? (
            <Mic className="h-2.5 w-2.5" />
          ) : (
            <MicOff className="h-2.5 w-2.5" />
          )}
          {microphoneActive ? 'Mic' : 'Muted'}
        </span>
        <span
          className={cn(
            'inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[9px] font-medium',
            isActive ? 'bg-accent/20 text-accent' : 'bg-surface-light text-text-secondary'
          )}
        >
          <VideoOff className="h-2.5 w-2.5" />
          {isActive ? 'Camera' : 'Off'}
        </span>
      </div>
    </div>
  )
}
