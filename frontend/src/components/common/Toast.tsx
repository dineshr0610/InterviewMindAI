import { motion, AnimatePresence } from 'framer-motion'
import { AlertCircle, CheckCircle, Info } from 'lucide-react'
import { useEffect } from 'react'

export interface ToastProps {
  id: string
  type: 'error' | 'success' | 'info'
  message: string
  duration?: number
  onClose: (id: string) => void
}

export function Toast({ id, type, message, duration = 3000, onClose }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => onClose(id), duration)
    return () => clearTimeout(timer)
  }, [id, duration, onClose])

  const bgColor =
    type === 'error'
      ? 'bg-red-500/10 border-red-500/20'
      : type === 'success'
        ? 'bg-green-500/10 border-green-500/20'
        : 'bg-blue-500/10 border-blue-500/20'

  const Icon =
    type === 'error' ? AlertCircle : type === 'success' ? CheckCircle : Info

  const iconColor =
    type === 'error'
      ? 'text-red-400'
      : type === 'success'
        ? 'text-green-400'
        : 'text-blue-400'

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={`flex items-center gap-3 rounded-lg border px-4 py-3 ${bgColor} backdrop-blur-sm`}
    >
      <Icon className={`h-5 w-5 flex-shrink-0 ${iconColor}`} />
      <p className="text-sm text-text">{message}</p>
    </motion.div>
  )
}

export function ToastContainer({
  toasts,
  onClose,
}: {
  toasts: ToastProps[]
  onClose: (id: string) => void
}) {
  return (
    <div className="fixed right-0 top-0 z-50 flex flex-col gap-3 p-4">
      <AnimatePresence>
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            {...toast}
            onClose={onClose}
          />
        ))}
      </AnimatePresence>
    </div>
  )
}
