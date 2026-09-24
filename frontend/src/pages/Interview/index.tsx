import { useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Header } from '../../components/layout/Header'
import { Footer } from '../../components/layout/Footer'
import { PerformanceAnalysis } from '../../components/interview/PerformanceAnalysis'
import { ChatTimeline } from '../../components/interview/ChatTimeline'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { Button } from '../../components/ui/Button'
import { useInterviewContext } from '../../context/InterviewContext'
import { ToastContainer } from '../../components/common/Toast'
import type { ToastProps } from '../../components/common/Toast'
import { ChevronDown } from 'lucide-react'
import { motion } from 'framer-motion'

import { InterviewStatus } from '../../components/interview/InterviewStatus'
import { InterviewRoom } from '../../components/interview/InterviewRoom'
import { MediaReadinessGate } from '../../components/interview/MediaReadinessGate'
import { QuestionPanel } from '../../components/interview/QuestionPanel'
import { ResponsePanel } from '../../components/interview/ResponsePanel'
import { PerformancePanel } from '../../components/interview/PerformancePanel'
import { EndInterviewDialog } from '../../components/interview/EndInterviewDialog'
import { useMediaDevices } from '../../hooks/useMediaDevices'
import { useInterviewerState } from '../../hooks/useInterviewerState'

export default function InterviewPage() {
  const navigate = useNavigate()
  const {
    session,
    isLoading,
    error,
    submitAnswer,
    endInterview,
  } = useInterviewContext()

  const [toasts, setToasts] = useState<ToastProps[]>([])
  const [showTimeline, setShowTimeline] = useState(false)
  const [showEndDialog, setShowEndDialog] = useState(false)
  const [gatePassed, setGatePassed] = useState(false)
  const [recording, setRecording] = useState(false)
  const [questionSpeaking, setQuestionSpeaking] = useState(false)
  const [isListeningForInput, setIsListeningForInput] = useState(false)

  const media = useMediaDevices()

  // Request camera/mic access once when the interview page loads. This never
  // blocks the interview — if it fails we gracefully fall back to text.
  useEffect(() => {
    media.startCamera()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!session) {
      navigate('/')
    }
  }, [session, navigate])

  useEffect(() => {
    if (error) {
      addToast('error', error)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [error])

  const addToast = (
    type: 'error' | 'success' | 'info',
    message: string
  ) => {
    const id = `toast-${Date.now()}`
    setToasts((prev) => [
      ...prev,
      {
        id,
        type,
        message,
        onClose: removeToast,
      },
    ])
  }

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  const currentQuestion = session?.messages
    .filter((m) => m.type === 'question')
    .pop()

  const lastAnswer = session?.messages
    .filter((m) => m.type === 'answer')
    .pop()

  const questionCount = session
    ? session.messages.filter((m) => m.type === 'question').length
    : 0

  const hasActiveQuestion = Boolean(currentQuestion)
  const hasCurrentEvaluation = Boolean(session?.currentEvaluation)

  const interviewerCtl = useInterviewerState({
    hasQuestion: hasActiveQuestion,
    ttsSpeaking: questionSpeaking,
    isSubmitting: isLoading,
    isRecording: recording,
    hasCurrentAnswer: hasCurrentEvaluation,
    isListeningForInput,
  })

  const handleSubmitAnswer = async (answer: string) => {
    setQuestionSpeaking(false)
    interviewerCtl.setListening(false)
    try {
      const result = await submitAnswer(answer)

      if (result?.completed) {
        addToast(
          'success',
          'Interview complete! Generating your performance analysis.'
        )
      } else {
        addToast('success', 'Answer submitted! AI is evaluating...')
        interviewerCtl.onNextQuestion()
      }
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : 'Failed to submit answer'

      addToast('error', errorMsg)
    }
  }

  const handleRequestEnd = () => {
    setShowEndDialog(true)
  }

  const handleConfirmEnd = async () => {
    try {
      await endInterview()
      setShowEndDialog(false)
      addToast('success', 'Interview ended.')
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : 'Failed to end interview'
      addToast('error', errorMsg)
      setShowEndDialog(false)
    }
  }

  if (!session) {
    return null
  }

  const isComplete = Boolean(session.endTime)

  // ================================================================
  // COMPLETED INTERVIEW
  // ================================================================
  if (isComplete) {
    return (
      <div className="flex flex-col min-h-screen">
        <Header title={`Interview Complete - ${session.role}`} />

        <main className="flex-1 px-4 py-8 md:px-6 lg:px-8">
          <div className="max-w-5xl mx-auto">
            <PerformanceAnalysis
              messages={session.messages}
              candidateName={session.candidateName}
              role={session.role}
              startTime={session.startTime}
              endTime={session.endTime}
              resumeUsed={session.resumeUsed}
            />

            <div className="mt-6 flex justify-center">
              <Button variant="outline" onClick={() => navigate('/')}>
                Start New Interview
              </Button>
            </div>
          </div>
        </main>

        <Footer />

        <ToastContainer toasts={toasts} onClose={removeToast} />
      </div>
    )
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Header title={`Interview - ${session.role}`} />

      <main className="flex-1 px-4 py-6 md:px-6 lg:px-8">
        <div className="mx-auto max-w-[1500px]">
          <InterviewStatus
            candidateName={session.candidateName}
            resumeUsed={Boolean(session.resumeUsed)}
            questionNumber={questionCount}
            totalQuestions={null}
            startTime={session.startTime}
            onEndInterview={handleRequestEnd}
            endDisabled={isLoading}
          />

          {session.messages.length === 0 ? (
            <div className="flex items-center justify-center py-16">
              <LoadingSpinner message="Loading your first question..." />
            </div>
          ) : (
            <div className="grid gap-6 lg:grid-cols-5">
              {/* LEFT: Candidate interaction area (question + answer) */}
              <div className="space-y-5 order-2 lg:order-1 lg:col-span-3">
                {currentQuestion && (
                  <QuestionPanel
                    question={currentQuestion.content}
                    questionNumber={questionCount}
                    totalQuestions={null}
                    topic={session.topic}
                    onSpeakStateChange={(speaking) => {
                      setQuestionSpeaking(speaking)
                      if (speaking && hasActiveQuestion) {
                        interviewerCtl.promptQuestion(currentQuestion.content)
                      } else if (!speaking) {
                        interviewerCtl.reset()
                      }
                    }}
                  />
                )}

                {currentQuestion && !isLoading && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                  >
                    <ResponsePanel
                      onSubmit={handleSubmitAnswer}
                      isLoading={isLoading}
                      micLevel={media.getMicrophoneLevel()}
                      microphoneActive={media.isMicrophoneActive}
                      onMicUnavailable={() => {
                        addToast(
                          'info',
                          'Microphone is off. Turn on your microphone to use voice input.'
                        )
                      }}
                      onSpeakingStateChange={(listening) => {
                        setRecording(listening)
                        setIsListeningForInput(listening)
                        interviewerCtl.setListening(listening)
                      }}
                    />
                  </motion.div>
                )}

                {lastAnswer && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="p-4 rounded-lg bg-surface/50 border border-surface-light"
                  >
                    <p className="text-sm font-semibold text-text-secondary mb-2">
                      Your Last Answer
                    </p>
                    <p className="text-text leading-relaxed">
                      {lastAnswer.content}
                    </p>
                  </motion.div>
                )}

                {session.messages.length > 1 && (
                  <button
                    onClick={() => setShowTimeline(!showTimeline)}
                    className="w-full flex items-center justify-between px-4 py-3 rounded-lg bg-surface border border-surface-light hover:border-primary transition-colors"
                  >
                    <span className="font-semibold text-text">
                      Chat History
                    </span>

                    <ChevronDown
                      className={`h-4 w-4 transition-transform ${
                        showTimeline ? 'rotate-180' : ''
                      }`}
                    />
                  </button>
                )}

                {showTimeline && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="rounded-lg bg-surface/50 border border-surface-light p-4 max-h-96 overflow-y-auto"
                  >
                    <ChatTimeline messages={session.messages} />
                  </motion.div>
                )}
              </div>

              {/* RIGHT: Interviewer area (video + controls + performance) */}
              <div className="space-y-5 order-1 lg:order-2 lg:col-span-2">
                {!gatePassed ? (
                  <div className="rounded-xl border border-surface-light bg-surface/40 p-4">
                    <MediaReadinessGate
                      status={media.readiness}
                      hasCamera={media.isCameraActive}
                      hasMicrophone={media.isMicrophoneActive}
                      hasAudio={media.speakerEnabled}
                      onContinue={() => {
                        setGatePassed(true)
                        if (media.readiness === 'denied' || media.readiness === 'unavailable') {
                          addToast(
                            'info',
                            'Camera unavailable. Continuing with audio/text interview.'
                          )
                        }
                      }}
                      onRetry={async () => {
                        await media.retryAccess()
                      }}
                    />
                  </div>
                ) : (
                  <InterviewRoom
                    status={interviewerCtl.status}
                    micLevel={media.getMicrophoneLevel()}
                    cameraActive={media.isCameraActive}
                    cameraEnabled={media.cameraEnabled}
                    microphoneEnabled={media.microphoneEnabled}
                    microphoneActive={media.isMicrophoneActive}
                    speakerEnabled={media.speakerEnabled}
                    onToggleCamera={media.toggleCamera}
                    onToggleMicrophone={media.toggleMicrophone}
                    onToggleSpeaker={media.toggleSpeaker}
                    setVideoElement={media.setVideoElement}
                  />
                )}

                <PerformancePanel
                  evaluation={session.currentEvaluation || null}
                  isLoading={isLoading}
                  hasActiveQuestion={hasActiveQuestion}
                  hasAnswerInProgress={recording}
                />
              </div>
            </div>
          )}
        </div>
      </main>

      <Footer />

      <EndInterviewDialog
        open={showEndDialog}
        isLoading={isLoading}
        onConfirm={handleConfirmEnd}
        onCancel={() => setShowEndDialog(false)}
      />

      <ToastContainer toasts={toasts} onClose={removeToast} />
    </div>
  )
}
