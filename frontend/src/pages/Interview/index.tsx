import { useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Header } from '../../components/layout/Header'
import { Footer } from '../../components/layout/Footer'
import { QuestionCard } from '../../components/interview/QuestionCard'
import { EvaluationPanel } from '../../components/interview/EvaluationPanel'
import { AnswerForm } from '../../components/interview/AnswerForm'
import { ChatTimeline } from '../../components/interview/ChatTimeline'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { Button } from '../../components/ui/Button'
import { useInterviewContext } from '../../context/InterviewContext'
import { ToastContainer } from '../../components/common/Toast'
import type { ToastProps } from '../../components/common/Toast'
import { LogOut, ChevronDown } from 'lucide-react'
import { motion } from 'framer-motion'

export default function InterviewPage() {
  const navigate = useNavigate()
  const { session, isLoading, error, submitAnswer, endInterview } = useInterviewContext()
  const [toasts, setToasts] = useState<ToastProps[]>([])
  const [showTimeline, setShowTimeline] = useState(false)
  const [hasSubmittedAnswer, setHasSubmittedAnswer] = useState(false)

  // Redirect to home if no active session
  useEffect(() => {
    if (!session) {
      navigate('/')
    }
  }, [session, navigate])

  // Show error toast if error occurs
  useEffect(() => {
    if (error) {
      addToast('error', error)
    }
  }, [error])

  const addToast = (type: 'error' | 'success' | 'info', message: string) => {
    const id = `toast-${Date.now()}`
    const toast: ToastProps = {
      id,
      type,
      message,
      onClose: removeToast,
    }
    setToasts((prev) => [...prev, toast])
  }

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  const handleSubmitAnswer = async (answer: string) => {
    try {
      await submitAnswer(answer)
      setHasSubmittedAnswer(true)
      addToast('success', 'Answer submitted! AI is evaluating...')
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to submit answer'
      addToast('error', errorMsg)
    }
  }

  const handleEndInterview = async () => {
    if (window.confirm('Are you sure you want to end the interview? Your progress will be saved.')) {
      try {
        await endInterview()
        addToast('success', 'Interview ended. Thank you for practicing!')
        setTimeout(() => navigate('/'), 2000)
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to end interview'
        addToast('error', errorMsg)
      }
    }
  }

  if (!session) {
    return null
  }

  const currentQuestion = session.messages
    .filter((m) => m.type === 'question')
    .pop()

  const lastAnswer = session.messages
    .filter((m) => m.type === 'answer')
    .pop()

  const questionCount = session.messages.filter((m) => m.type === 'question').length

  return (
    <div className="flex flex-col min-h-screen">
      <Header title={`Interview - ${session.role}`} />

      <main className="flex-1 px-4 py-8 md:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Session Info */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-4 rounded-lg bg-surface/50 border border-surface-light"
          >
            <div>
              <p className="text-sm text-text-secondary">Candidate</p>
              <p className="font-semibold text-text">{session.candidateName}</p>
            </div>
            <div>
              <p className="text-sm text-text-secondary">Questions Answered</p>
              <p className="font-semibold text-text">{questionCount}</p>
            </div>
            <div>
              <p className="text-sm text-text-secondary">Interview Duration</p>
              <p className="font-semibold text-text">
                {Math.floor((Date.now() - session.startTime) / 1000)}s
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleEndInterview}
              disabled={isLoading}
            >
              <LogOut className="h-4 w-4" />
              End Interview
            </Button>
          </motion.div>

          {/* Loading State */}
          {session.messages.length === 0 ? (
            <div className="flex items-center justify-center py-16">
              <LoadingSpinner message="Loading your first question..." />
            </div>
          ) : (
            <div className="grid lg:grid-cols-3 gap-6">
              {/* Main Content - Left & Center */}
              <div className="lg:col-span-2 space-y-6">
                {/* Current Question */}
                {currentQuestion && (
                  <QuestionCard
                    question={currentQuestion.content}
                    questionNumber={questionCount}
                  />
                )}

                {/* Answer Form */}
                {currentQuestion && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    <AnswerForm
                      onSubmit={handleSubmitAnswer}
                      isLoading={isLoading}
                    />
                  </motion.div>
                )}

                {/* Last Answer Display */}
                {lastAnswer && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="p-4 rounded-lg bg-surface/50 border border-surface-light"
                  >
                    <p className="text-sm font-semibold text-text-secondary mb-2">Your Last Answer</p>
                    <p className="text-text leading-relaxed">{lastAnswer.content}</p>
                  </motion.div>
                )}
              </div>

              {/* Right Sidebar */}
              <div className="space-y-6">
                {/* Evaluation Panel */}
                <EvaluationPanel
                  evaluation={session.currentEvaluation || null}
                  isLoading={isLoading && hasSubmittedAnswer}
                />

                {/* Timeline Toggle */}
                {session.messages.length > 1 && (
                  <button
                    onClick={() => setShowTimeline(!showTimeline)}
                    className="w-full flex items-center justify-between px-4 py-3 rounded-lg bg-surface border border-surface-light hover:border-primary transition-colors"
                  >
                    <span className="font-semibold text-text">Chat History</span>
                    <ChevronDown
                      className={`h-4 w-4 transition-transform ${showTimeline ? 'rotate-180' : ''}`}
                    />
                  </button>
                )}

                {/* Timeline */}
                {showTimeline && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="rounded-lg bg-surface/50 border border-surface-light p-4 max-h-96 overflow-y-auto"
                  >
                    <ChatTimeline messages={session.messages} />
                  </motion.div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      <Footer />

      {/* Toast Container */}
      <ToastContainer toasts={toasts} onClose={removeToast} />
    </div>
  )
}
