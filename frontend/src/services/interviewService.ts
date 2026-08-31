import api from './api'
import { StartInterviewRequest, AnswerRequest } from '../types'

function topicFromRole(role?: string): string {
  const r = (role || '').toLowerCase().trim()

  if (r.includes('frontend') || r.includes('front-end') || r.includes('react') || r.includes('ui')) {
    return 'Frontend Development'
  }

  if (r.includes('backend') || r.includes('back-end') || r.includes('api') || r.includes('server')) {
    return 'Backend Development'
  }

  if (r.includes('full stack') || r.includes('full-stack') || r.includes('fullstack')) {
    return 'Full Stack Development'
  }

  if (r.includes('python')) {
    return 'Python Development'
  }

  if (r.includes('java')) {
    return 'Java Development'
  }

  if (r.includes('data scientist') || r.includes('data science')) {
    return 'Data Science'
  }

  if (r.includes('machine learning') || r.includes('ml engineer')) {
    return 'Machine Learning'
  }

  if (r.includes('devops') || r.includes('cloud')) {
    return 'DevOps and Cloud'
  }

  if (r.includes('software engineer') || r.includes('software developer')) {
    return 'Software Engineering'
  }

  if (r.includes('mobile') || r.includes('android') || r.includes('ios')) {
    return 'Mobile Development'
  }

  if (r.includes('database') || r.includes('dba')) {
    return 'Database Engineering'
  }

  return role?.trim() || 'Software Engineering'
}

export const interviewService = {
  /**
   * Start a new interview session
   */
  async startInterview(request: StartInterviewRequest) {
    const role = request.job_role?.trim() || 'Software Engineer'
    const topicValue = request.topic && request.topic.trim() ? request.topic.trim() : topicFromRole(role)

    const response = await api.post('/api/interview/start', {
      candidate_name: request.candidate_name,
      role: role,
      topic: topicValue,
      difficulty: request.difficulty || 'Easy',
      resume_text: request.resume_text || undefined,
    })

    const resData = response.data
    return resData.data || resData
  },

  /**
   * Upload a PDF resume and return the extracted clean text
   */
  async uploadResume(file: File) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/api/interview/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    const resData = response.data
    return resData.data || resData
  },

  async submitAnswer(request: AnswerRequest) {
    const response = await api.post('/api/interview/answer', {
      interview_id: request.interview_id,
      answer: request.answer,
    })

    const resData = response.data
    return resData.data || resData
  },

  async getHistory(interviewId: string) {
    const response = await api.get(`/api/interview/${interviewId}/history`)
    const resData = response.data
    return resData.data || resData
  },

  async endInterview(interviewId: string) {
    const response = await api.post(`/api/interview/${interviewId}/end`)
    const resData = response.data
    return resData.data || resData
  },

  async checkHealth() {
    const response = await api.get('/api/health')
    const resData = response.data
    return resData.data || resData
  },
}
