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
  topic?: string
  startTime: number
  endTime?: number
  messages: ChatMessage[]
  currentEvaluation?: Evaluation
  isLoading: boolean
  error?: string
  results?: InterviewHistory
}

export interface InterviewHistoryMessage {
  question: string
  answer: string | null
  score: number | null
  feedback: string | null
  strengths: string | null
  improvements: string | null
  next_question: string | null
}

export interface InterviewHistory {
  candidate_name: string
  role: string
  topic: string
  difficulty: string
  status: string
  messages: InterviewHistoryMessage[]
}

export interface StartInterviewRequest {
  candidate_name: string
  job_role: string
  topic?: string
  difficulty?: 'Easy' | 'Medium' | 'Hard'
  max_questions?: number
}

export interface AnswerRequest {
  interview_id: string
  answer: string
}
