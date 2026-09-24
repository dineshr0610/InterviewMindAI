import { useCallback, useEffect, useRef, useState } from 'react'

export type SpeechStatus = 'idle' | 'recording' | 'processing'

interface SpeechRecognitionLike {
  lang: string
  interimResults: boolean
  continuous: boolean
  maxAlternatives: number
  onresult: ((event: SpeechRecognitionEventLike) => void) | null
  onerror: ((event: { error?: string }) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
}

interface SpeechRecognitionEventLike {
  resultIndex: number
  results: ArrayLike<{
    isFinal: boolean
    0: { transcript: string }
  }>
}

function getRecognition(): SpeechRecognitionLike | null {
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike
    webkitSpeechRecognition?: new () => SpeechRecognitionLike
  }
  const Ctor = w.SpeechRecognition || w.webkitSpeechRecognition
  return Ctor ? new Ctor() : null
}

export interface UseSpeechToTextResult {
  status: SpeechStatus
  isSupported: boolean
  /** Accumulated FINAL transcript segments (committed speech). */
  transcript: string
  /** The live/partial transcript that is still being recognized. */
  interimTranscript: string
  error: string | null
  startListening: () => void
  stopListening: () => void
  resetTranscript: () => void
}

export function useSpeechToText(): UseSpeechToTextResult {
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null)
  // True while the user wants to keep listening (auto-restart guard).
  const activeRef = useRef(false)
  // Set to true on fatal errors so onend does not restart recognition.
  const fatalRef = useRef(false)
  // Keeps the latest transcript available inside the recognition callbacks.
  const finalTranscriptRef = useRef('')
  const [status, setStatus] = useState<SpeechStatus>('idle')
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)

  const supported = typeof window !== 'undefined' && !!getRecognition()

  const resetTranscript = useCallback(() => {
    finalTranscriptRef.current = ''
    setTranscript('')
    setInterimTranscript('')
  }, [])

  const stopListening = useCallback(() => {
    // Prevent auto-restart: the user explicitly stopped.
    activeRef.current = false
    setInterimTranscript('')
    const recognition = recognitionRef.current
    if (recognition) {
      setStatus('processing')
      try {
        recognition.stop()
      } catch {
        // If stop fails the onend handler will clean up.
      }
    } else {
      setStatus('idle')
    }
  }, [])

  const startListening = useCallback(() => {
    if (!supported) {
      setError("Voice input isn't supported in this browser. You can continue with text.")
      return
    }

    // Stop any existing recognition instance before starting a clean one.
    const existing = recognitionRef.current
    if (existing) {
      try {
        existing.stop()
      } catch {
        // Ignore; we replace it below.
      }
    }

    const recognition = getRecognition()
    if (!recognition) {
      setError(
        "Voice input isn't supported in this browser. You can continue with text."
      )
      return
    }
    recognitionRef.current = recognition
    activeRef.current = true
    fatalRef.current = false

    recognition.lang = 'en-US'
    recognition.interimResults = true
    recognition.continuous = true
    recognition.maxAlternatives = 1

    recognition.onresult = (event) => {
      let interim = ''
      // Note: `transcript` is never cleared by results — finals accumulate.
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i]
        if (result.isFinal && result[0]?.transcript) {
          const segment = result[0].transcript.trim()
          if (segment) {
            finalTranscriptRef.current = finalTranscriptRef.current
              ? `${finalTranscriptRef.current} ${segment}`
              : segment
          }
        } else if (result[0]?.transcript) {
          interim += result[0].transcript
        }
      }
      setTranscript(finalTranscriptRef.current)
      setInterimTranscript(interim.trim())
    }

    recognition.onerror = (event) => {
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        activeRef.current = false
        fatalRef.current = true
        setError(
          'Microphone access was denied. You can continue typing your answer.'
        )
      } else if (event.error === 'no-speech') {
        setError('No speech detected.')
      } else if (event.error === 'audio-capture') {
        activeRef.current = false
        fatalRef.current = true
        setError(
          'No microphone was found. You can continue typing your answer.'
        )
      } else if (event.error === 'aborted') {
        // Sending `stop()` produces an aborted error — the user stopped, so
        // do not surface this as a user-facing failure.
        return
      } else {
        setError(
          "Couldn't recognize speech. Please try again or continue typing."
        )
      }
    }

    recognition.onend = () => {
      setInterimTranscript('')
      recognitionRef.current = null
      // If the user still wants to listen and there was no fatal error, restart
      // the recognizer safely (browsers stop recognition automatically).
      if (activeRef.current && !fatalRef.current) {
        startListening()
        return
      }
      setStatus('idle')
    }

    setError(null)
    setStatus('recording')
    try {
      recognition.start()
    } catch {
      activeRef.current = false
      fatalRef.current = true
      setError(
        "Couldn't recognize speech. Please try again or continue typing."
      )
      setStatus('idle')
    }
  }, [supported])

  // Stop on unmount.
  useEffect(() => {
    return () => {
      activeRef.current = false
      recognitionRef.current?.stop()
    }
  }, [])

  return {
    status,
    isSupported: supported,
    transcript,
    interimTranscript,
    error,
    startListening,
    stopListening,
    resetTranscript,
  }
}
