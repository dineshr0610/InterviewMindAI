import { useEffect, useRef, useState } from 'react'
import { TextArea } from '../ui/TextArea'
import { Button } from '../ui/Button'
import { Mic, Send, Square } from 'lucide-react'
import { useSpeechToText } from '../../hooks/useSpeechToText'

interface AnswerFormProps {
  onSubmit: (answer: string) => Promise<void>
  isLoading: boolean
  disabled?: boolean
}

export function AnswerForm({ onSubmit, isLoading, disabled }: AnswerFormProps) {
  const [answer, setAnswer] = useState('')
  const [speechErrorVisible, setSpeechErrorVisible] = useState(false)
  const lastAppendedTranscript = useRef('')

  const {
    status,
    isSupported,
    transcript,
    error: speechError,
    startListening,
    stopListening,
    resetTranscript,
  } = useSpeechToText()

  const isRecording = status === 'recording'
  const isProcessing = status === 'processing'
  const hasSpoken = transcript.length > 0

  // Append finalized speech transcripts into the existing answer field, so
  // voice input is just another way to add text to the single answer.
  useEffect(() => {
    if (transcript && transcript !== lastAppendedTranscript.current) {
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

  // Surface voice errors inline but never block text input.
  useEffect(() => {
    if (speechError) {
      setSpeechErrorVisible(true)
    }
  }, [speechError])

  const onFormSubmit = async () => {
    if (!answer.trim()) return

    try {
      await onSubmit(answer)
      setAnswer('')
      resetTranscript()
      lastAppendedTranscript.current = ''
      setSpeechErrorVisible(false)
    } catch (error) {
      console.error('[AnswerForm] Submission error:', error)
    }
  }

  const handleVoiceToggle = () => {
    if (isRecording) {
      stopListening()
    } else {
      setSpeechErrorVisible(false)
      startListening()
    }
  }

  const textDisabled = isLoading || disabled

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onFormSubmit()
      }}
      className="space-y-4"
    >
      <TextArea
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
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

      {isSupported && (
        <div className="flex flex-col gap-2">
          {!isRecording && !isProcessing && (
            <Button
              type="button"
              variant="outline"
              onClick={handleVoiceToggle}
              disabled={textDisabled}
              className="w-full"
            >
              <Mic className="h-4 w-4" />
              {hasSpoken ? 'Speak More' : 'Speak Answer'}
            </Button>
          )}

          {isRecording && (
            <Button
              type="button"
              variant="outline"
              onClick={handleVoiceToggle}
              disabled={textDisabled}
              className="w-full border-error text-error hover:bg-error/10"
            >
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-error opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-error" />
              </span>
              Listening...
            </Button>
          )}

          {isProcessing && (
            <Button
              type="button"
              variant="outline"
              disabled
              className="w-full"
            >
              <Square className="h-4 w-4" />
              Processing speech...
            </Button>
          )}
        </div>
      )}

      {!isSupported && (
        <p className="text-sm text-text-secondary">
          Voice input isn't supported in this browser. You can continue with
          text.
        </p>
      )}

      <Button
        type="submit"
        isLoading={isLoading}
        disabled={disabled}
        className="w-full"
      >
        <Send className="h-4 w-4" />
        Submit Answer
      </Button>
    </form>
  )
}
