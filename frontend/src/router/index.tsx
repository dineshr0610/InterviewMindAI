import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import HomePage from '../pages/Home'
import InterviewPage from '../pages/Interview'
import NotFoundPage from '../pages/NotFound'

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/interview" element={<InterviewPage />} />
        <Route path="/404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
