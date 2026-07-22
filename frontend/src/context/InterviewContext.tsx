import React, { createContext, useContext } from 'react'
import { useInterview } from '../hooks/useInterview'
import { InterviewSession } from '../types'

interface InterviewContextType {
  session: InterviewSession | null
  isLoading: boolean
  error: string | null
  startInterview: (candidateName: string, jobRole: string) => Promise<any>
  submitAnswer: (answer: string) => Promise<any>
  endInterview: () => Promise<void>
  resetSession: () => void
}

const InterviewContext = createContext<InterviewContextType | undefined>(undefined)

export function InterviewProvider({ children }: { children: React.ReactNode }) {
  const interview = useInterview()

  return (
    <InterviewContext.Provider value={interview}>
      {children}
    </InterviewContext.Provider>
  )
}

export function useInterviewContext() {
  const context = useContext(InterviewContext)
  if (!context) {
    throw new Error('useInterviewContext must be used within InterviewProvider')
  }
  return context
}
