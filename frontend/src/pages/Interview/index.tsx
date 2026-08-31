import { useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Header } from '../../components/layout/Header'
import { Footer } from '../../components/layout/Footer'
import { QuestionCard } from '../../components/interview/QuestionCard'
import { EvaluationPanel } from '../../components/interview/EvaluationPanel'
import { PerformanceAnalysis } from '../../components/interview/PerformanceAnalysis'
import { AnswerForm } from '../../components/interview/AnswerForm'
import { ChatTimeline } from '../../components/interview/ChatTimeline'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { QuestionTimer } from '../../components/interview/QuestionTimer'
import { Button } from '../../components/ui/Button'
import { useInterviewContext } from '../../context/InterviewContext'
import { ToastContainer } from '../../components/common/Toast'
import type { ToastProps } from '../../components/common/Toast'
import { LogOut, ChevronDown } from 'lucide-react'
import { motion } from 'framer-motion'

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

  useEffect(() => {
    if (!session) {
      navigate('/')
    }
  }, [session, navigate])

  useEffect(() => {
    if (error) {
      addToast('error', error)
    }
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

  const handleSubmitAnswer = async (answer: string) => {
    try {
      const result = await submitAnswer(answer)

      if (result?.completed) {
        addToast(
          'success',
          'Interview complete! Generating your performance analysis.'
        )
      } else {
        addToast('success', 'Answer submitted! AI is evaluating...')
      }
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : 'Failed to submit answer'

      addToast('error', errorMsg)
    }
  }

  const handleEndInterview = async () => {
    if (
      window.confirm(
        'Are you sure you want to end the interview? Your progress will be saved.'
      )
    ) {
      try {
        await endInterview()
        addToast('success', 'Interview ended.')
      } catch (err) {
        const errorMsg =
          err instanceof Error ? err.message : 'Failed to end interview'
        addToast('error', errorMsg)
      }
    }
  }

  if (!session) {
    return null
  }

  const isComplete = Boolean(session.endTime)

  const currentQuestion = session.messages
    .filter((m) => m.type === 'question')
    .pop()

  const lastAnswer = session.messages
    .filter((m) => m.type === 'answer')
    .pop()

  const questionCount = session.messages.filter(
    (m) => m.type === 'question'
  ).length

  // ================================================================
  // COMPLETED INTERVIEW
  // IMPORTANT: No QuestionCard and NO AnswerForm are rendered here.
  // This permanently prevents the Q3 -> Q3 -> limit reached problem.
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
            />

            <div className="mt-6 flex justify-center">
              <Button
                variant="outline"
                onClick={() => navigate('/')}
              >
                Start New Interview
              </Button>
            </div>
          </div>
        </main>

        <Footer />

        <ToastContainer
          toasts={toasts}
          onClose={removeToast}
        />
      </div>
    )
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Header title={`Interview - ${session.role}`} />

      <main className="flex-1 px-4 py-8 md:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-4 rounded-lg bg-surface/50 border border-surface-light"
          >
            <div>
              <p className="text-sm text-text-secondary">Candidate</p>
              <p className="font-semibold text-text">
                {session.candidateName}
              </p>
            </div>

            <div>
              <p className="text-sm text-text-secondary">
                Questions Answered
              </p>
              <p className="font-semibold text-text">
                {session.messages.filter((m) => m.type === 'answer').length} / 3
              </p>
            </div>            <QuestionTimer
              questionKey={`question-${session.messages.filter((m) => m.type === 'question').length}`}
              timeLimitSeconds={60}
            />

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

          {session.messages.length === 0 ? (
            <div className="flex items-center justify-center py-16">
              <LoadingSpinner message="Loading your first question..." />
            </div>
          ) : (
            <div className="grid lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                {currentQuestion && (
                  <QuestionCard
                    question={currentQuestion.content}
                    questionNumber={questionCount}
                  />
                )}

                {currentQuestion && !isLoading && (
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

                {lastAnswer && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
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
              </div>

              <div className="space-y-6">
                <EvaluationPanel
                  evaluation={session.currentEvaluation || null}
                  isLoading={isLoading}
                />

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
            </div>
          )}
        </div>
      </main>

      <Footer />

      <ToastContainer
        toasts={toasts}
        onClose={removeToast}
      />
    </div>
  )
}


