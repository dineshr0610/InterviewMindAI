import type { ReactNode } from 'react'
import { cn } from '../../utils/cn'
import { Mic, MicOff, Video, VideoOff, Volume2, VolumeX } from 'lucide-react'

interface InterviewControlsProps {
  cameraEnabled: boolean
  isCameraActive: boolean
  microphoneEnabled: boolean
  isMicrophoneActive: boolean
  speakerEnabled: boolean
  onToggleCamera: () => void
  onToggleMicrophone: () => void
  onToggleSpeaker: () => void
  compact?: boolean
}

function ControlButton({
  label,
  active,
  danger,
  onClick,
  children,
  title,
}: {
  label: string
  active: boolean
  danger?: boolean
  onClick: () => void
  children: ReactNode
  title: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      aria-pressed={active}
      className={cn(
        'flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-all duration-200',
        danger
          ? 'border-error/50 bg-error/10 text-error hover:bg-error/20'
          : active
            ? 'border-surface-light bg-surface-light text-text hover:bg-surface-light/80'
            : 'border-surface-light bg-surface/60 text-text-secondary hover:text-text hover:bg-surface-light/50'
      )}
    >
      {children}
      <span className="hidden sm:inline">{label}</span>
    </button>
  )
}

export function InterviewControls({
  cameraEnabled,
  isCameraActive,
  microphoneEnabled,
  isMicrophoneActive,
  speakerEnabled,
  onToggleCamera,
  onToggleMicrophone,
  onToggleSpeaker,
}: InterviewControlsProps) {
  const camOff = !isCameraActive
  const micOff = !isMicrophoneActive

  return (
    <div className="flex flex-wrap items-center gap-2">
      <ControlButton
        label={micOff ? 'Muted' : 'Mic'}
        active={isMicrophoneActive}
        danger={micOff}
        onClick={onToggleMicrophone}
        title={microphoneEnabled ? 'Toggle microphone' : 'Microphone unavailable'}
      >
        {isMicrophoneActive ? (
          <Mic className="h-4 w-4" />
        ) : (
          <MicOff className="h-4 w-4" />
        )}
      </ControlButton>

      <ControlButton
        label={camOff ? 'Camera Off' : 'Camera'}
        active={isCameraActive}
        danger={camOff}
        onClick={onToggleCamera}
        title={cameraEnabled ? 'Toggle camera' : 'Camera unavailable'}
      >
        {isCameraActive ? (
          <Video className="h-4 w-4" />
        ) : (
          <VideoOff className="h-4 w-4" />
        )}
      </ControlButton>

      <ControlButton
        label={speakerEnabled ? 'Speaker' : 'Muted Audio'}
        active={speakerEnabled}
        onClick={onToggleSpeaker}
        title="Toggle speaker"
      >
        {speakerEnabled ? (
          <Volume2 className="h-4 w-4" />
        ) : (
          <VolumeX className="h-4 w-4" />
        )}
      </ControlButton>
    </div>
  )
}
