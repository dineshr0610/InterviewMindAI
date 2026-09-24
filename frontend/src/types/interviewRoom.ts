export type InterviewerStatus =
  | 'idle'
  | 'thinking'
  | 'speaking'
  | 'listening'
  | 'evaluating'
  | 'nextQuestion'

export interface MediaDeviceState {
  cameraEnabled: boolean
  microphoneEnabled: boolean
  speakerEnabled: boolean
  cameraError: string | null
  microphoneError: string | null
  isCameraActive: boolean
  isMicrophoneActive: boolean
  hasPermissions: boolean
}
