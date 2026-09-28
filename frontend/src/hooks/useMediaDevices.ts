import { useCallback, useEffect, useRef, useState } from 'react'
import { MediaDeviceState } from '../types/interviewRoom'

export interface MediaDevicesResult extends MediaDeviceState {
  readiness: 'checking' | 'ready' | 'denied' | 'unavailable'
  startCamera: () => Promise<void>
  stopCamera: () => void
  toggleCamera: () => void
  toggleMicrophone: () => void
  toggleSpeaker: () => void
  getMicrophoneLevel: () => number
  retryAccess: () => Promise<void>
  skipAccess: () => void
  setVideoElement: (el: HTMLVideoElement | null) => void
}

export function useMediaDevices(): MediaDevicesResult {
  const [state, setState] = useState<MediaDeviceState>({
    cameraEnabled: false,
    microphoneEnabled: false,
    speakerEnabled: true,
    cameraError: null,
    microphoneError: null,
    isCameraActive: false,
    isMicrophoneActive: false,
    hasPermissions: false,
  })

  const [readiness, setReadiness] = useState<
    'checking' | 'ready' | 'denied' | 'unavailable'
  >('checking')

  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const previewStreamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const levelIntervalRef = useRef<number | null>(null)
  const activeLevelRef = useRef(0)
  const skippedRef = useRef(false)

  const setVideoElement = useCallback((el: HTMLVideoElement | null) => {
    videoRef.current = el
    // Always attach the VIDEO-ONLY preview stream so the candidate's
    // microphone audio can never reach the speakers via this element.
    if (el && previewStreamRef.current) {
      el.srcObject = previewStreamRef.current
    }
  }, [])

  const stopAllTracks = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    previewStreamRef.current = null
  }, [])

  const stopLevelMonitor = useCallback(() => {
    if (levelIntervalRef.current !== null) {
      window.clearInterval(levelIntervalRef.current)
      levelIntervalRef.current = null
    }
    activeLevelRef.current = 0
    audioContextRef.current?.close().catch(() => {})
    audioContextRef.current = null
    analyserRef.current = null
  }, [])

  const startLevelMonitor = useCallback((stream: MediaStream) => {
    stopLevelMonitor()
    try {
      const AudioCtx =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext?: typeof AudioContext })
          .webkitAudioContext
      const ctx = new AudioCtx()
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 256
      const source = ctx.createMediaStreamSource(stream)
      source.connect(analyser)
      audioContextRef.current = ctx
      analyserRef.current = analyser
      const buf = new Uint8Array(analyser.frequencyBinCount)
      levelIntervalRef.current = window.setInterval(() => {
        analyser.getByteFrequencyData(buf)
        const sum = buf.reduce((a, b) => a + b, 0)
        activeLevelRef.current = sum / buf.length / 255
      }, 60)
    } catch {
      // Level visualization is optional; never break the interview if it fails.
    }
  }, [stopLevelMonitor])

  const getMicrophoneLevel = useCallback(() => {
    return activeLevelRef.current
  }, [])

  const startCamera = useCallback(async () => {
    if (skippedRef.current) {
      setReadiness('unavailable')
      return
    }
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        setState((s) => ({
          ...s,
          cameraError: 'Camera access is not supported in this browser.',
        }))
        setReadiness('unavailable')
        return
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })

      stopAllTracks()

      // Keep the FULL combined stream for recording / analysis, but route a
      // VIDEO-ONLY media stream to the camera preview. This guarantees the
      // candidate's microphone is never able to reach the speakers through
      // the preview <video> element.
      streamRef.current = stream
      const videoTrack = stream.getVideoTracks()[0]
      const audioTrack = stream.getAudioTracks()[0]
      const videoOnlyStream = videoTrack
        ? new MediaStream([videoTrack])
        : new MediaStream()
      previewStreamRef.current = videoOnlyStream

      if (videoRef.current) {
        videoRef.current.srcObject = videoOnlyStream
      }

      // Handle when the user stops hardware capture externally.
      videoTrack?.addEventListener('ended', () => {
        setState((s) => ({ ...s, isCameraActive: false }))
      })
      audioTrack?.addEventListener('ended', () => {
        setState((s) => ({ ...s, isMicrophoneActive: false }))
        stopLevelMonitor()
      })

      startLevelMonitor(stream)
      setState({
        cameraEnabled: true,
        microphoneEnabled: true,
        speakerEnabled: true,
        cameraError: null,
        microphoneError: null,
        isCameraActive: true,
        isMicrophoneActive: true,
        hasPermissions: true,
      })
      setReadiness('ready')
    } catch (err) {
      const message =
        err instanceof DOMException && err.name === 'NotAllowedError'
          ? 'Camera and microphone permission was denied.'
          : 'Camera and microphone could not be accessed.'
      setState((s) => ({
        ...s,
        cameraError: message,
        microphoneError: message,
        hasPermissions: false,
      }))
      setReadiness('denied')
    }
  }, [startLevelMonitor, stopAllTracks, stopLevelMonitor])

  const stopCamera = useCallback(() => {
    stopAllTracks()
    stopLevelMonitor()
    setState((s) => ({
      ...s,
      isCameraActive: false,
      isMicrophoneActive: false,
    }))
  }, [stopAllTracks, stopLevelMonitor])

  const toggleCamera = useCallback(() => {
    setState((s) => {
      if (s.isCameraActive) {
        const track = streamRef.current?.getVideoTracks()[0]
        if (track) track.enabled = false
        return { ...s, isCameraActive: false, cameraEnabled: false }
      }
      const track = streamRef.current?.getVideoTracks()[0]
      if (track) track.enabled = true
      return { ...s, isCameraActive: true, cameraEnabled: true }
    })
  }, [])

  const toggleMicrophone = useCallback(() => {
    setState((s) => {
      if (s.isMicrophoneActive) {
        const track = streamRef.current?.getAudioTracks()[0]
        if (track) track.enabled = false
        stopLevelMonitor()
        return { ...s, isMicrophoneActive: false, microphoneEnabled: false }
      }
      const track = streamRef.current?.getAudioTracks()[0]
      if (track) track.enabled = true
      activeLevelRef.current = 0
      if (streamRef.current) startLevelMonitor(streamRef.current)
      return { ...s, isMicrophoneActive: true, microphoneEnabled: true }
    })
  }, [startLevelMonitor, stopLevelMonitor])

  const toggleSpeaker = useCallback(() => {
    setState((s) => ({ ...s, speakerEnabled: !s.speakerEnabled }))
  }, [])

  const retryAccess = useCallback(async () => {
    setReadiness('checking')
    await startCamera()
  }, [startCamera])

  const skipAccess = useCallback(() => {
    skippedRef.current = true
    setReadiness('unavailable')
  }, [])

  useEffect(() => {
    return () => {
      stopAllTracks()
      stopLevelMonitor()
    }
  }, [stopAllTracks, stopLevelMonitor])

  return {
    ...state,
    readiness,
    startCamera,
    stopCamera,
    toggleCamera,
    toggleMicrophone,
    toggleSpeaker,
    getMicrophoneLevel,
    retryAccess,
    skipAccess,
    setVideoElement,
  }
}
