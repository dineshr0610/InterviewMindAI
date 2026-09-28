import { useCallback, useEffect, useRef, useState } from 'react'

export interface UseTextToSpeechResult {
  speaking: boolean
  isSupported: boolean
  speak: (text: string) => void
  stop: () => void
}

export function useTextToSpeech(): UseTextToSpeechResult {
  const [speaking, setSpeaking] = useState(false)
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)

  const supported =
    typeof window !== 'undefined' && 'speechSynthesis' in window

  useEffect(() => {
    return () => {
      if (supported) {
        window.speechSynthesis.cancel()
      }
    }
  }, [supported])

  const stop = useCallback(() => {
    if (supported) {
      window.speechSynthesis.cancel()
    }
    setSpeaking(false)
  }, [supported])

  const speak = useCallback(
    (text: string) => {
      if (!supported || !text.trim()) {
        return
      }

      window.speechSynthesis.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      utteranceRef.current = utterance
      utterance.rate = 1
      utterance.pitch = 1
      utterance.volume = 1
      utterance.lang = 'en-US'

      utterance.onend = () => setSpeaking(false)
      utterance.onerror = () => setSpeaking(false)

      setSpeaking(true)
      window.speechSynthesis.speak(utterance)
    },
    [supported]
  )

  return { speaking, isSupported: supported, speak, stop }
}
