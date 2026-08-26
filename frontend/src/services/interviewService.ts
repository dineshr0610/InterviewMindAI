import api from './api'
import { StartInterviewRequest, AnswerRequest } from '../types'

export const interviewService = {
  /**
   * Start a new interview session
   */
  async startInterview(request: StartInterviewRequest) {
    const topicValue = request.topic && request.topic.trim() ? request.topic.trim() : request.job_role || 'General Technical'
    const response = await api.post('/api/interview/start', {
      candidate_name: request.candidate_name,
      role: request.job_role,
      topic: topicValue,
      difficulty: request.difficulty || 'Easy',
      max_questions: request.max_questions || 5,
    })
    const resData = response.data
    return resData.data || resData
  },

  /**
   * Submit an answer and get evaluation
   */
  async submitAnswer(request: AnswerRequest) {
    const response = await api.post('/api/interview/answer', {
      interview_id: request.interview_id,
      answer: request.answer,
    })
    const resData = response.data
    return resData.data || resData
  },

  /**
   * Get interview history
   */
  async getHistory(interviewId: string) {
    const response = await api.get(`/api/interview/${interviewId}/history`)
    const resData = response.data
    return resData.data || resData
  },

  /**
   * End an interview session
   */
  async endInterview(interviewId: string) {
    const response = await api.post(`/api/interview/${interviewId}/end`)
    const resData = response.data
    return resData.data || resData
  },

  /**
   * Check backend health
   */
  async checkHealth() {
    const response = await api.get('/api/health')
    const resData = response.data
    return resData.data || resData
  },
}
