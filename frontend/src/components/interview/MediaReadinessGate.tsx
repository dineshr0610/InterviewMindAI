import { motion } from 'framer-motion'
import { Check, X, RefreshCw, ArrowRight } from 'lucide-react'

interface MediaReadinessGateProps {
  status: 'checking' | 'ready' | 'denied' | 'unavailable'
  hasCamera: boolean
  hasMicrophone: boolean
  hasAudio: boolean
  onContinue: () => void
  onRetry: () => void
}

function itemState(ok: boolean | undefined) {
  if (ok === true) return { ok: true }
  if (ok === false) return { ok: false }
  return { ok: false, unknown: true }
}

export function MediaReadinessGate({
  status,
  hasCamera,
  hasMicrophone,
  hasAudio,
  onContinue,
  onRetry,
}: MediaReadinessGateProps) {
  const camera = itemState(hasCamera)
  const mic = itemState(hasMicrophone)
  const audio = itemState(hasAudio)

  if (status === 'checking') {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex flex-col items-center justify-center gap-4 py-10 text-center"
      >
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        <p className="text-text-secondary text-sm">Preparing your interview environment...</p>
      </motion.div>
    )
  }

  if (status === 'ready') {
    return (
      <div className="flex flex-col items-center gap-6 py-6 text-center">
        <div>
          <h3 className="text-lg font-semibold text-text">Prepare for your interview</h3>
          <p className="text-sm text-text-secondary">
            Check your camera and microphone before you begin.
          </p>
        </div>

        <div className="w-full max-w-xs space-y-2">
          <ReadinessRow label="Camera" ok={camera.ok} />
          <ReadinessRow label="Microphone" ok={mic.ok} />
          <ReadinessRow label="Audio Output" ok={audio.ok} />
        </div>

        <button
          type="button"
          onClick={onContinue}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 font-medium text-background transition-colors hover:bg-primary-dark"
        >
          Continue
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    )
  }

  if (status === 'denied') {
    return (
      <div className="flex flex-col items-center gap-6 py-6 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-error/15">
          <X className="h-6 w-6 text-error" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-text">Camera unavailable</h3>
          <p className="text-sm text-text-secondary max-w-xs">
            Your camera could not be accessed. You can still continue with the
            text-based interview.
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-3">
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-2 rounded-lg border-2 border-primary px-5 py-2.5 font-medium text-primary transition-colors hover:bg-primary/10"
          >
            <RefreshCw className="h-4 w-4" />
            Try Again
          </button>
          <button
            type="button"
            onClick={onContinue}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 font-medium text-background transition-colors hover:bg-primary-dark"
          >
            Continue with Text
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        <p className="text-xs text-warning">
          Continuing with audio/text interview.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-4 py-6 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-light">
        <X className="h-6 w-6 text-text-secondary" />
      </div>
      <div>
        <h3 className="text-lg font-semibold text-text">Camera unavailable</h3>
        <p className="text-sm text-text-secondary max-w-xs">
          Camera access is not supported in this environment. Continuing with
          audio/text interview.
        </p>
      </div>
      <button
        type="button"
        onClick={onContinue}
        className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 font-medium text-background transition-colors hover:bg-primary-dark"
      >
        Continue
        <ArrowRight className="h-4 w-4" />
      </button>
    </div>
  )
}

function ReadinessRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-surface-light bg-surface/60 px-4 py-2.5">
      <span className="text-sm text-text">{label}</span>
      {ok ? (
        <span className="flex items-center gap-1.5 text-sm text-accent">
          <Check className="h-4 w-4" />
          Ready
        </span>
      ) : (
        <span className="flex items-center gap-1.5 text-sm text-warning">
          <X className="h-4 w-4" />
          Unavailable
        </span>
      )}
    </div>
  )
}
