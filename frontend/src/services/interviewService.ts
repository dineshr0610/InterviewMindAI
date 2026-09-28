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

  if (r.includes('data analyst') || r.includes('data analysis') || r.includes('analytics')) {
    return 'Data Analysis & SQL'
  }

  if (r.includes('ai engineer') || r.includes('artificial intelligence') || r.includes('genai') || r.includes('llm')) {
    return 'Artificial Intelligence & LLMs'
  }

  if (r.includes('machine learning') || r.includes('ml engineer')) {
    return 'Machine Learning'
  }

  if (r.includes('database') || r.includes('sql') || r.includes('dba')) {
    return 'Database Development & SQL'
  }

  if (r.includes('devops') || r.includes('cloud')) {
    return 'DevOps & Cloud Engineering'
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
   * Upload a PDF or DOCX resume and return the extracted clean text
   */
  async uploadResume(file: File, role?: string) {
    const formData = new FormData()
    formData.append('file', file)
    if (role) {
      formData.append('role', role)
    }

    const response = await api.post('/api/interview/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    const resData = response.data
    return resData.data || resData
  },

  /**
   * Analyze resume against selected role (Module 1 analysis)
   */
  async analyzeResume(resumeText: string, role: string, candidateName?: string) {
    const response = await api.post('/api/interview/resume/analyze', {
      resume_text: resumeText,
      role,
      candidate_name: candidateName || 'Candidate',
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
