import { useEffect, useRef, useState } from 'react'
import { TextArea } from '../ui/TextArea'
import { Button } from '../ui/Button'
import { Mic, Send, Loader2 } from 'lucide-react'
import { useSpeechToText } from '../../hooks/useSpeechToText'

interface ResponsePanelProps {
  onSubmit: (answer: string) => Promise<void>
  isLoading: boolean
  disabled?: boolean
  micLevel: number
  microphoneActive: boolean
  onMicUnavailable?: () => void
  onSpeakingStateChange?: (listening: boolean) => void
}

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export function ResponsePanel({
  onSubmit,
  isLoading,
  disabled,
  micLevel,
  microphoneActive,
  onMicUnavailable,
  onSpeakingStateChange,
}: ResponsePanelProps) {
  const [answer, setAnswer] = useState('')
  const [elapsed, setElapsed] = useState(0)
  const [speechErrorVisible, setSpeechErrorVisible] = useState(false)
  // True once the user edits the textarea, freezing auto-append until the next
  // voice session starts, so we never clobber manual typing.
  const editingRef = useRef(false)
  const lastAppendedTranscript = useRef('')
  const interimRef = useRef('')
  const startTimeRef = useRef<number | null>(null)

  const {
    status,
    isSupported,
    transcript,
    interimTranscript,
    error: speechError,
    startListening,
    stopListening,
    resetTranscript,
  } = useSpeechToText()

  const isListening = status === 'recording'
  const isProcessing = status === 'processing'

  // Report speaking state upward so the AI interviewer / performance panel
  // reflect that the candidate is currently answering.
  useEffect(() => {
    onSpeakingStateChange?.(isListening)
  }, [isListening, onSpeakingStateChange])

  // Speaking timer while voice input is active.
  useEffect(() => {
    if (!isListening) {
      startTimeRef.current = null
      return
    }
    startTimeRef.current = Date.now()
    setElapsed(0)
    const interval = window.setInterval(() => {
      if (startTimeRef.current) {
        setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000))
      }
    }, 500)
    return () => window.clearInterval(interval)
  }, [isListening])

  // Append finalized speech transcripts into the existing answer field.
  useEffect(() => {
    if (!editingRef.current && transcript && transcript !== lastAppendedTranscript.current) {
      const newSegment = transcript
        .slice(lastAppendedTranscript.current.length)
        .trim()
      if (newSegment) {
        setAnswer((prev) => {
          const prefix = prev ? prev + ' ' : ''
          return prefix + newSegment
        })
      }
      lastAppendedTranscript.current = transcript
    }
  }, [transcript])

  // Keep the latest interim transcript available for committing on stop.
  useEffect(() => {
    interimRef.current = interimTranscript
  }, [interimTranscript])

  // Surface voice errors inline but never block text input.
  useEffect(() => {
    if (speechError) {
      setSpeechErrorVisible(true)
    }
  }, [speechError])

  const onFormSubmit = async () => {
    if (isListening) {
      stopListening()
    }
    if (answer.trim()) {
      const finalAnswer = answer.trim()
      try {
        await onSubmit(finalAnswer)
        setAnswer('')
        resetTranscript()
        lastAppendedTranscript.current = ''
        setSpeechErrorVisible(false)
        setElapsed(0)
        editingRef.current = false
      } catch (error) {
        console.error('[ResponsePanel] Submission error:', error)
      }
    }
  }

  const handleStartListening = () => {
    setSpeechErrorVisible(false)
    if (!microphoneActive) {
      onMicUnavailable?.()
      return
    }
    editingRef.current = false
    setElapsed(0)
    startListening()
  }

  const handleStopListening = () => {
    stopListening()
    // Commit any trailing interim speech so a short answer isn't lost.
    const trailing = interimRef.current.trim()
    if (trailing) {
      setAnswer((prev) => {
        const prefix = prev ? prev + ' ' : ''
        return prefix + trailing
      })
    }
    interimRef.current = ''
    setElapsed(0)
    editingRef.current = false
  }

  // While listening and the user hasn't taken over editing, show the live
  // interim transcript temporarily appended to the committed answer.
  const displayAnswer =
    isListening && !editingRef.current && interimTranscript
      ? answer + (answer ? ' ' : '') + interimTranscript
      : answer

  const textDisabled = isLoading || disabled
  const canSubmit = answer.trim().length > 0

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onFormSubmit()
      }}
      className="space-y-4"
    >
      <TextArea
        value={displayAnswer}
        onChange={(e) => {
          editingRef.current = true
          setAnswer(e.target.value)
        }}
        placeholder="Type your answer here..."
        rows={4}
        disabled={textDisabled}
        className="resize-none"
      />

      {speechErrorVisible && speechError && (
        <p className="text-sm text-error" role="alert">
          {speechError}
        </p>
      )}

      {isSupported && !isListening && isProcessing && (
        <Button type="button" variant="outline" disabled className="w-full">
          <Loader2 className="h-4 w-4 animate-spin" />
          Processing speech...
        </Button>
      )}

      {isSupported && isListening && (
        <div className="flex flex-col gap-2 rounded-lg border border-error/30 bg-error/5 p-3">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-error opacity-75" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-error" />
              </span>
              <span className="text-sm font-semibold text-error">Listening</span>
              <span className="font-mono text-sm font-semibold text-error">
                {formatTime(elapsed)}
              </span>
            </div>

            {/* Mic level visualization driven by actual microphone input */}
            <div className="flex items-end gap-[3px] h-5">
              {Array.from({ length: 14 }).map((_, i) => {
                const active = i < Math.max(1, Math.round(micLevel * 14))
                return (
                  <span
                    key={i}
                    className="w-[3px] rounded-full bg-error transition-all duration-75"
                    style={{
                      height: active ? '100%' : '25%',
                      opacity: active ? 1 : 0.25,
                    }}
                  />
                )
              })}
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleStopListening}
            className="w-full border-error text-error hover:bg-error/10"
          >
            Stop Speaking
          </Button>
        </div>
      )}

      {isSupported && !isListening && !isProcessing && (
        <Button
          type="button"
          variant="outline"
          onClick={handleStartListening}
          disabled={textDisabled}
          className="w-full"
        >
          <Mic className="h-4 w-4" />
          Speak Answer
        </Button>
      )}

      {!isSupported && (
        <p className="text-sm text-text-secondary">
          Voice input isn't supported in this browser. You can continue with text.
        </p>
      )}

      <Button
        type="submit"
        isLoading={isLoading}
        disabled={disabled || !canSubmit}
        className="w-full"
      >
        <Send className="h-4 w-4" />
        Submit Answer
      </Button>
    </form>
  )
}
