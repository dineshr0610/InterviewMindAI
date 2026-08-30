import { useState, useCallback, useRef } from 'react'
import { InterviewSession, ChatMessage } from '../types'
import { interviewService } from '../services/interviewService'
import { parseEvaluation } from '../utils/parser'

const MAX_QUESTIONS = 3

function roleTopic(role: string): string {
  const r = role.toLowerCase()

  if (r.includes('frontend') || r.includes('front-end')) {
    return 'Frontend Developer: JavaScript, TypeScript, React, HTML, CSS, browser fundamentals, REST APIs, state management, performance, accessibility, testing, and frontend system design'
  }

  if (r.includes('backend') || r.includes('back-end')) {
    return 'Backend Developer: APIs, databases, SQL, authentication, authorization, caching, concurrency, scalability, system design, testing, and backend architecture'
  }

  if (r.includes('full stack') || r.includes('fullstack')) {
    return 'Full Stack Developer: JavaScript/TypeScript, React, APIs, databases, authentication, backend architecture, testing, deployment, performance, and system design'
  }

  if (r.includes('data scientist')) {
    return 'Data Scientist: Python, statistics, probability, machine learning, feature engineering, model evaluation, SQL, experimentation, and data analysis'
  }

  if (r.includes('machine learning') || r.includes('ml engineer')) {
    return 'Machine Learning Engineer: Python, machine learning algorithms, model evaluation, feature engineering, data pipelines, deployment, MLOps, and system design'
  }

  if (r.includes('devops') || r.includes('cloud')) {
    return 'DevOps/Cloud Engineer: Linux, networking, Docker, Kubernetes, CI/CD, cloud architecture, monitoring, security, infrastructure, and reliability'
  }

  if (r.includes('dsa') || r.includes('algorithm')) {
    return 'Data Structures and Algorithms: arrays, strings, linked lists, stacks, queues, trees, graphs, hashing, sorting, searching, recursion, dynamic programming, and complexity analysis'
  }

  return `${role}: core technical concepts, practical problem solving, architecture, debugging, testing, performance, security, and real-world engineering practices`
}

export function useInterview() {
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submittingRef = useRef(false)

  const startInterview = useCallback(
    async (candidateName: string, jobRole: string) => {
      try {
        setIsLoading(true)
        setError(null)
        submittingRef.current = false

        const response = await interviewService.startInterview({
          candidate_name: candidateName,
          job_role: jobRole,
          topic: roleTopic(jobRole),
          difficulty: 'Medium',
          max_questions: MAX_QUESTIONS,
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

      if (submittingRef.current || isLoading) {
        return null
      }

      const trimmedAnswer = answer.trim()

      if (trimmedAnswer.length < 10) {
        throw new Error('Answer must be at least 10 characters.')
      }

      const questionMessages = session.messages.filter(
        (m) => m.type === 'question'
      )

      const answeredQuestionCount = session.messages.filter(
        (m) => m.type === 'answer'
      ).length

      if (answeredQuestionCount >= MAX_QUESTIONS) {
        throw new Error('This interview has already reached 3 questions.')
      }

      const currentQuestion =
        questionMessages[questionMessages.length - 1]

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

        const nextQ =
          response.next_question ||
          response.nextQuestion ||
          evaluation.nextQuestion

        const newAnsweredCount = answeredQuestionCount + 1

        /*
         * Q3 is the final question.
         * Never add another question after Q3.
         */
        if (newAnsweredCount >= MAX_QUESTIONS) {
          try {
            await interviewService.endInterview(session.id)
          } catch (endError) {
            console.warn(
              '[useInterview] Could not automatically end interview:',
              endError
            )
          }

          setSession((prev) =>
            prev
              ? {
                  ...prev,
                  currentEvaluation: evaluation,
                  endTime: Date.now(),
                }
              : null
          )

          return {
            evaluation,
            nextQuestion: null,
            completed: true,
          }
        }

        /*
         * Only add a new question when one exists.
         * The current question remains the question that was answered.
         */
        if (nextQ) {
          const existingQuestions = session.messages
            .filter((m) => m.type === 'question')
            .map((m) => m.content.trim())

          /*
           * Protect the UI if the backend accidentally returns
           * the exact same question again.
           */
          const duplicateQuestion = existingQuestions.some(
            (q) => q.toLowerCase() === nextQ.trim().toLowerCase()
          )

          if (!duplicateQuestion) {
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

            throw new Error(
              'The AI returned a duplicate question. Please restart the interview.'
            )
          }
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

    try {
      setIsLoading(true)
      setError(null)

      await interviewService.endInterview(session.id)

      setSession((prev) =>
        prev
          ? {
              ...prev,
              endTime: Date.now(),
            }
          : null
      )
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
