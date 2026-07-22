export interface Evaluation {
  score: number
  feedback: string
  strengths: string[]
  weaknesses: string[]
  nextQuestion?: string
  raw?: string
}

export interface ChatMessage {
  id: string
  type: 'question' | 'answer' | 'evaluation'
  content: string
  timestamp: number
  evaluation?: Evaluation
}

export interface InterviewSession {
  id: string
  candidateName: string
  role: string
  startTime: number
  endTime?: number
  messages: ChatMessage[]
  currentEvaluation?: Evaluation
  isLoading: boolean
  error?: string
}

export interface StartInterviewRequest {
  candidate_name: string
  job_role: string
}

export interface AnswerRequest {
  interview_id: string
  answer: string
}
