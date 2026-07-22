import { ChatMessage } from '../../types'
import { motion } from 'framer-motion'
import { MessageCircle, User, Check } from 'lucide-react'

interface ChatTimelineProps {
  messages: ChatMessage[]
}

export function ChatTimeline({ messages }: ChatTimelineProps) {
  return (
    <div className="space-y-4">
      {messages.length === 0 ? (
        <p className="text-center text-text-secondary py-8">Interview questions will appear here...</p>
      ) : (
        messages.map((message, index) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="flex items-start gap-3"
          >
            {/* Icon */}
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-surface-light">
              {message.type === 'question' ? (
                <MessageCircle className="h-4 w-4 text-primary" />
              ) : message.type === 'answer' ? (
                <User className="h-4 w-4 text-text-secondary" />
              ) : (
                <Check className="h-4 w-4 text-accent" />
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="text-xs text-text-secondary mb-1 capitalize">
                {message.type === 'question' ? 'Interview Question' : message.type === 'answer' ? 'Your Answer' : 'Evaluation'}
              </div>
              <p className="text-sm text-text bg-surface-light rounded px-3 py-2 break-words">
                {message.content.substring(0, 150)}
                {message.content.length > 150 ? '...' : ''}
              </p>
            </div>
          </motion.div>
        ))
      )}
    </div>
  )
}
