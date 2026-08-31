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
  transcript: string
  error: string | null
  startListening: () => void
  stopListening: () => void
  resetTranscript: () => void
}

export function useSpeechToText(): UseSpeechToTextResult {
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null)
  const [status, setStatus] = useState<SpeechStatus>('idle')
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)

  const supported = typeof window !== 'undefined' && !!getRecognition()

  useEffect(() => {
    return () => {
      recognitionRef.current?.stop()
    }
  }, [])

  const stopListening = useCallback(() => {
    const recognition = recognitionRef.current
    if (recognition) {
      setStatus('processing')
      try {
        recognition.stop()
      } catch {
        // If stop fails the onend handler will clean up.
      }
    }
  }, [])

  const startListening = useCallback(() => {
    if (!supported) {
      setError("Voice input isn't supported in this browser. You can continue with text.")
      return
    }

    const recognition = getRecognition()
    if (!recognition) {
      setError(
        "Voice input isn't supported in this browser. You can continue with text."
      )
      return
    }
    recognitionRef.current = recognition

    recognition.lang = 'en-US'
    recognition.interimResults = false
    recognition.continuous = false
    recognition.maxAlternatives = 1

    recognition.onresult = (event) => {
      let finalText = ''
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i]
        if (result.isFinal && result[0]?.transcript) {
          finalText += result[0].transcript
        }
      }
      finalText = finalText.trim()
      if (finalText) {
        setTranscript((prev) => (prev ? `${prev} ${finalText}` : finalText))
      }
    }

    recognition.onerror = (event) => {
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        setError(
          'Microphone access was denied. You can continue typing your answer.'
        )
      } else if (event.error === 'no-speech') {
        setError('No speech detected.')
      } else if (event.error === 'audio-capture') {
        setError(
          'No microphone was found. You can continue typing your answer.'
        )
      } else {
        setError(
          "Couldn't recognize speech. Please try again or continue typing."
        )
      }
      setStatus('idle')
    }

    recognition.onend = () => {
      // A session ended (either the user pressed stop, speech ended, or the
      // browser auto-stopped). Always return to idle so the microphone never
      // gets stuck in the recording state. Transcripts have already been
      // finalized via onresult, so they remain available for "Speak More".
      setStatus('idle')
      recognitionRef.current = null
    }

    setError(null)
    setStatus('recording')
    try {
      recognition.start()
    } catch {
      setError(
        "Couldn't recognize speech. Please try again or continue typing."
      )
      setStatus('idle')
    }
  }, [supported])

  const resetTranscript = useCallback(() => {
    setTranscript('')
  }, [])

  return {
    status,
    isSupported: supported,
    transcript,
    error,
    startListening,
    stopListening,
    resetTranscript,
  }
}
