import axios from 'axios'

const API_BASE_URL = (import.meta as any).env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log('[API] Request:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('[API] Request error:', error)
    return Promise.reject(error)
  }
)

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log('[API] Response:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('[API] Response error:', error.response?.status, error.message)
    return Promise.reject(error)
  }
)

export default api
