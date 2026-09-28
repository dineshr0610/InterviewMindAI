import { AIInterviewer } from './AIInterviewer'
import { CandidateCamera } from './CandidateCamera'
import { InterviewControls } from './InterviewControls'
import type { InterviewerStatus } from '../../types/interviewRoom'

interface InterviewRoomProps {
  status: InterviewerStatus
  micLevel: number
  cameraActive: boolean
  cameraEnabled: boolean
  microphoneEnabled: boolean
  microphoneActive: boolean
  speakerEnabled: boolean
  onToggleCamera: () => void
  onToggleMicrophone: () => void
  onToggleSpeaker: () => void
  setVideoElement: (el: HTMLVideoElement | null) => void
}

export function InterviewRoom({
  status,
  micLevel,
  cameraActive,
  cameraEnabled,
  microphoneEnabled,
  microphoneActive,
  speakerEnabled,
  onToggleCamera,
  onToggleMicrophone,
  onToggleSpeaker,
  setVideoElement,
}: InterviewRoomProps) {
  return (
    <div className="space-y-3">
      <div className="relative">
        <AIInterviewer status={status} micLevel={micLevel} />

        {/* Picture-in-picture candidate self-view */}
        <div className="absolute bottom-10 right-3 z-20 w-[26%] max-w-[170px] sm:w-[24%]">
          <CandidateCamera
            isActive={cameraActive}
            microphoneActive={microphoneActive}
            setVideoElement={setVideoElement}
          />
        </div>
      </div>

      {/* Compact video-call controls */}
      <div className="flex items-center justify-center">
        <InterviewControls
          cameraEnabled={cameraEnabled}
          isCameraActive={cameraActive}
          microphoneEnabled={microphoneEnabled}
          isMicrophoneActive={microphoneActive}
          speakerEnabled={speakerEnabled}
          onToggleCamera={onToggleCamera}
          onToggleMicrophone={onToggleMicrophone}
          onToggleSpeaker={onToggleSpeaker}
        />
      </div>
    </div>
  )
}
