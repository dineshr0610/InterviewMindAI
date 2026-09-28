import { motion } from 'framer-motion'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import { MessageCircle, Volume2, Square, FileText, Zap } from 'lucide-react'
import { useTextToSpeech } from '../../hooks/useTextToSpeech'

interface QuestionPanelProps {
  question: string
  questionNumber: number
  totalQuestions: number | null
  topic?: string
  difficulty?: string
  onSpeakStateChange?: (speaking: boolean) => void
}

export function QuestionPanel({
  question,
  questionNumber,
  totalQuestions,
  topic,
  difficulty = 'Easy',
  onSpeakStateChange,
}: QuestionPanelProps) {
  const { speaking, isSupported, speak, stop } = useTextToSpeech()

  const handleListen = () => {
    if (speaking) {
      stop()
      onSpeakStateChange?.(false)
    } else {
      onSpeakStateChange?.(true)
      speak(question)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      key={question}
    >
      <Card className="space-y-4">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-primary/20">
            <MessageCircle className="h-6 w-6 text-primary" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                AI Interviewer
              </span>
              {topic && (
                <span className="inline-flex items-center gap-1 rounded-full bg-surface-light/60 px-2 py-0.5 text-[11px] font-medium text-text-secondary">
                  <FileText className="h-3 w-3" />
                  {topic}
                </span>
              )}
              {difficulty && (
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold border ${
                    difficulty === 'Hard'
                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      : difficulty === 'Medium'
                        ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                        : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  }`}
                >
                  <Zap className="h-3 w-3" />
                  Adaptive: {difficulty}
                </span>
              )}
            </div>

            <p className="text-lg font-semibold text-text leading-relaxed">
              &ldquo;{question}&rdquo;
            </p>

            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-text-secondary">
              {totalQuestions && totalQuestions > 0 ? (
                <span className="font-medium">
                  Question {questionNumber} of {totalQuestions}
                </span>
              ) : (
                <span className="font-medium">Question {questionNumber}</span>
              )}
            </div>
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
