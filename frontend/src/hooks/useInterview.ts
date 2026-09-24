import { useState, useCallback, useRef } from 'react'
import { InterviewSession, ChatMessage, InterviewHistory } from '../types'
import { interviewService } from '../services/interviewService'
import { parseEvaluation } from '../utils/parser'

export function useInterview() {
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submittingRef = useRef(false)

  const startInterview = useCallback(
    async (
      candidateName: string,
      jobRole: string,
      topic?: string,
      difficulty?: 'Easy' | 'Medium' | 'Hard',
      resumeText?: string,
      resumeFile?: string
    ) => {
      try {
        setIsLoading(true)
        setError(null)
        submittingRef.current = false

        const response = await interviewService.startInterview({
          candidate_name: candidateName,
          job_role: jobRole,
          // Let the backend select a role-aware baseline topic unless the
          // candidate explicitly selected a technical topic.
          topic: topic || undefined,
          difficulty: difficulty || 'Easy',
          resume_text: resumeText,
        })

        const initialQuestion = response.question || response.first_question

        if (!initialQuestion) {
          throw new Error('Backend did not return the first interview question.')
        }

        const initialMessages: ChatMessage[] = [
          {
            id: 'question-1',
            type: 'question',
            content: initialQuestion,
            timestamp: Date.now(),
          },
        ]

        setSession({
          id: response.interview_id,
          candidateName,
          role: jobRole,
          topic: topic || jobRole,
          startTime: Date.now(),
          messages: initialMessages,
          isLoading: false,
          resumeFile: resumeFile || undefined,
          resumeContext: resumeText || undefined,
          resumeUsed: Boolean(resumeText),
        })

        return response
      } catch (err) {
        const errorMsg =
          err instanceof Error ? err.message : 'Failed to start interview'

        setError(errorMsg)
        console.error('[useInterview] Start interview error:', err)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    []
  )

  const submitAnswer = useCallback(
    async (answer: string) => {
      if (!session) {
        throw new Error('No active interview session')
      }

      if (session.endTime) {
        return {
          evaluation: session.currentEvaluation,
          nextQuestion: null,
          completed: true,
        }
      }

      if (submittingRef.current || isLoading) {
        return null
      }

      const trimmedAnswer = answer ? answer.trim() : ''
      if (trimmedAnswer.length < 10) {
        const validationError = 'Answer must be at least 10 non-whitespace characters.'
        setError(validationError)
        throw new Error(validationError)
      }

      const answeredQuestionCount = session.messages.filter(
        (m) => m.type === 'answer'
      ).length

      const currentQuestion = session.messages
        .filter((m) => m.type === 'question')
        .pop()

      if (!currentQuestion) {
        throw new Error('No active question found.')
      }

      try {
        submittingRef.current = true
        setIsLoading(true)
        setError(null)

        const answerMessage: ChatMessage = {
          id: `answer-${Date.now()}`,
          type: 'answer',
          content: trimmedAnswer,
          timestamp: Date.now(),
        }

        setSession((prev) =>
          prev
            ? {
              ...prev,
              messages: [...prev.messages, answerMessage],
            }
            : null
        )

        const response = await interviewService.submitAnswer({
          interview_id: session.id,
          answer: trimmedAnswer,
        })

        const evaluation = parseEvaluation(
          response.evaluation || response
        )

        const newAnsweredCount = answeredQuestionCount + 1

        // Store the evaluation permanently in the timeline.
        const evaluationMessage: ChatMessage = {
          id: `evaluation-${newAnsweredCount}-${Date.now()}`,
          type: 'evaluation',
          content: evaluation.feedback || `Score: ${evaluation.score}/10`,
          timestamp: Date.now(),
          evaluation,
        }

        const nextQ =
          response.next_question ||
          response.nextQuestion ||
          evaluation.nextQuestion

        if (nextQ) {
          const existingQuestions = session.messages
            .filter((m) => m.type === 'question')
            .map((q) => q.content.trim().toLowerCase())

          const duplicateQuestion = existingQuestions.includes(
            nextQ.trim().toLowerCase()
          )

          if (duplicateQuestion) {
            throw new Error(
              'The AI returned a duplicate question. Please restart the interview.'
            )
          }

          const questionMessage: ChatMessage = {
            id: `question-${newAnsweredCount + 1}-${Date.now()}`,
            type: 'question',
            content: nextQ.trim(),
            timestamp: Date.now(),
          }

          setSession((prev) =>
            prev
              ? {
                ...prev,
                messages: [
                  ...prev.messages,
                  evaluationMessage,
                  questionMessage,
                ],
                currentEvaluation: evaluation,
              }
              : null
          )
        } else {
          setSession((prev) =>
            prev
              ? {
                ...prev,
                messages: [...prev.messages, evaluationMessage],
                currentEvaluation: evaluation,
              }
              : null
          )
        }

        if (response.status === 'completed') {
          const results: InterviewHistory | undefined = await interviewService.getHistory(session.id)
          setSession((prev) => prev ? { ...prev, endTime: Date.now(), results } : null)
        }

        return {
          evaluation,
          nextQuestion: nextQ || null,
          completed: false,
        }
      } catch (err) {
        const errorMsg =
          err instanceof Error
            ? err.message
            : 'Failed to submit answer'

        setError(errorMsg)
        console.error('[useInterview] Submit answer error:', err)
        throw err
      } finally {
        submittingRef.current = false
        setIsLoading(false)
      }
    },
    [session, isLoading]
  )

  const endInterview = useCallback(async () => {
    if (!session) {
      throw new Error('No active interview session')
    }

    if (session.endTime) {
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      await interviewService.endInterview(session.id)

      let results: InterviewHistory | undefined
      try {
        results = await interviewService.getHistory(session.id)
      } catch (err) {
        console.warn('[useInterview] History fetch failed after end:', err)
      }

      setSession((prev) => (prev ? { ...prev, endTime: Date.now(), results } : null))
    } catch (err) {
      const errorMsg =
        err instanceof Error
          ? err.message
          : 'Failed to end interview'

      setError(errorMsg)
      console.error('[useInterview] End interview error:', err)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [session])

  const resetSession = useCallback(() => {
    submittingRef.current = false
    setSession(null)
    setError(null)
    setIsLoading(false)
  }, [])

  return {
    session,
    isLoading,
    error,
    startInterview,
    submitAnswer,
    endInterview,
    resetSession,
  }
}
