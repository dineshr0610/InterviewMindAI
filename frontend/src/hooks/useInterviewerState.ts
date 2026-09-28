import { useEffect, useRef, useState } from 'react'
import { InterviewerStatus } from '../types/interviewRoom'

interface UseInterviewerStateArgs {
  hasQuestion: boolean
  ttsSpeaking: boolean
  isSubmitting: boolean
  isRecording: boolean
  hasCurrentAnswer: boolean
  isListeningForInput: boolean
}

export interface InterviewerStateController {
  status: InterviewerStatus
  /** Ask a specific question (triggers thinking -> speaking). */
  promptQuestion: (text: string) => void
  /** Enter / exit the listening state (candidate is answering). */
  setListening: (active: boolean) => void
  /** Announce the AI has moved to the next question. */
  onNextQuestion: () => void
  /** Reset to idle. */
  reset: () => void
}

export function useInterviewerState({
  hasQuestion,
  ttsSpeaking,
  isSubmitting,
  isRecording,
  hasCurrentAnswer,
  isListeningForInput,
}: UseInterviewerStateArgs): InterviewerStateController {
  const [status, setStatus] = useState<InterviewerStatus>('idle')
  const [manual, setManual] = useState<InterviewerStatus | null>(null)
  const timerRef = useRef<number | null>(null)

  const clearTimer = () => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }

  useEffect(() => clearTimer, [])

  const promptQuestion = (text: string) => {
    clearTimer()
    setManual('thinking')
    // Brief "thinking" beat before speaking begins.
    if (ttsSpeaking) {
      setManual('speaking')
      return
    }
    timerRef.current = window.setTimeout(() => {
      if (text.trim()) {
        setManual('speaking')
      } else {
        setManual('idle')
      }
    }, 700)
  }

  const setListening = (active: boolean) => {
    clearTimer()
    if (active) {
      setManual('listening')
    } else {
      setManual(null)
    }
  }

  const onNextQuestion = () => {
    clearTimer()
    setManual('nextQuestion')
    timerRef.current = window.setTimeout(() => {
      setManual((prev) => (prev === 'nextQuestion' ? null : prev))
    }, 2600)
  }

  const reset = () => {
    clearTimer()
    setManual(null)
    setStatus('idle')
  }

  // Derive the effective status: manual state wins while set, otherwise
  // the automatic states driven by interview flow.
  let effective: InterviewerStatus = 'idle'

  if (manual) {
    effective = manual
  } else if (isSubmitting) {
    effective = 'evaluating'
  } else if (isRecording || isListeningForInput) {
    effective = 'listening'
  } else if (ttsSpeaking) {
    effective = 'speaking'
  } else if (hasQuestion && hasCurrentAnswer) {
    effective = 'idle'
  } else if (hasQuestion) {
    effective = 'idle'
  }

  useEffect(() => {
    setStatus(effective)
  }, [effective])

  return { status, promptQuestion, setListening, onNextQuestion, reset }
}
