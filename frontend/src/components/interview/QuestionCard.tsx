import { motion } from 'framer-motion'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import { MessageCircle, Volume2, Square } from 'lucide-react'
import { useTextToSpeech } from '../../hooks/useTextToSpeech'

interface QuestionCardProps {
  question: string
  questionNumber?: number
}

export function QuestionCard({ question, questionNumber }: QuestionCardProps) {
  const { speaking, isSupported, speak, stop } = useTextToSpeech()

  const handleListen = () => {
    if (speaking) {
      stop()
    } else {
      speak(question)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="space-y-4">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-primary/20">
            <MessageCircle className="h-6 w-6 text-primary" />
          </div>
          <div className="flex-1">
            {questionNumber && (
              <p className="text-xs font-semibold uppercase text-text-secondary mb-1">
                Question {questionNumber}
              </p>
            )}
            <p className="text-lg font-semibold text-text leading-relaxed">
              {question}
            </p>
          </div>
        </div>

        {isSupported && (
          <div className="flex justify-end">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleListen}
            >
              {speaking ? (
                <Square className="h-4 w-4" />
              ) : (
                <Volume2 className="h-4 w-4" />
              )}
              {speaking ? 'Stop' : 'Listen to Question'}
            </Button>
          </div>
        )}
      </Card>
    </motion.div>
  )
}
