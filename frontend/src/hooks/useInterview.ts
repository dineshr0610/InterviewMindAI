import { useState, useCallback } from 'react'
import { InterviewSession, ChatMessage } from '../types'
import { interviewService } from '../services/interviewService'
import { parseEvaluation } from '../utils/parser'

export function useInterview() {
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const startInterview = useCallback(
    async (candidateName: string, jobRole: string) => {
      try {
        setIsLoading(true)
        setError(null)

        const response = await interviewService.startInterview({
          candidate_name: candidateName,
          job_role: jobRole,
        })

        const initialQuestion = response.question || response.first_question
        const initialMessages: ChatMessage[] = initialQuestion
          ? [
              {
                id: `question-${Date.now()}`,
                type: 'question',
                content: initialQuestion,
                timestamp: Date.now(),
              },
            ]
          : []

        const newSession: InterviewSession = {
          id: response.interview_id,
          candidateName,
          role: jobRole,
          startTime: Date.now(),
          messages: initialMessages,
          isLoading: false,
        }

        setSession(newSession)
        return response
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to start interview'
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

      try {
        setIsLoading(true)
        setError(null)

        // Add user's answer to messages
        const answerMessage: ChatMessage = {
          id: `answer-${Date.now()}`,
          type: 'answer',
          content: answer,
          timestamp: Date.now(),
        }

        setSession((prev) =>
          prev ? { ...prev, messages: [...prev.messages, answerMessage] } : null
        )

        // Submit answer and get evaluation
        const response = await interviewService.submitAnswer({
          interview_id: session.id,
          answer,
        })

        // Parse evaluation (handles both object response and string text)
        const evaluation = parseEvaluation(response.evaluation || response)
        const nextQ = response.next_question || response.nextQuestion || evaluation.nextQuestion

        // Add next question to messages
        if (nextQ) {
          const questionMessage: ChatMessage = {
            id: `question-${Date.now()}`,
            type: 'question',
            content: nextQ,
            timestamp: Date.now(),
          }

          setSession((prev) =>
            prev
              ? {
                  ...prev,
                  messages: [...prev.messages, questionMessage],
                  currentEvaluation: evaluation,
                }
              : null
          )
        } else {
          setSession((prev) =>
            prev
              ? {
                  ...prev,
                  currentEvaluation: evaluation,
                }
              : null
          )
        }

        return {
          evaluation,
          nextQuestion: nextQ,
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to submit answer'
        setError(errorMsg)
        console.error('[useInterview] Submit answer error:', err)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [session]
  )

  const endInterview = useCallback(async () => {
    if (!session) {
      throw new Error('No active interview session')
    }

    try {
      setIsLoading(true)
      setError(null)

      await interviewService.endInterview(session.id)

      setSession((prev) => (prev ? { ...prev, endTime: Date.now() } : null))
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to end interview'
      setError(errorMsg)
      console.error('[useInterview] End interview error:', err)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [session])

  const resetSession = useCallback(() => {
    setSession(null)
    setError(null)
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
