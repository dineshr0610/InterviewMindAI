import { motion } from 'framer-motion'
import { Card } from '../ui/Card'
import { Evaluation } from '../../types'
import { Star, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react'

interface EvaluationPanelProps {
  evaluation: Evaluation | null
  isLoading: boolean
}

export function EvaluationPanel({ evaluation, isLoading }: EvaluationPanelProps) {
  if (isLoading) {
    return (
      <Card>
        <div className="space-y-4">
          <div className="h-8 bg-surface-light rounded animate-pulse" />
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-4 bg-surface-light rounded animate-pulse" />
            ))}
          </div>
        </div>
      </Card>
    )
  }

  if (!evaluation) {
    return (
      <Card className="flex items-center justify-center py-8">
        <p className="text-text-secondary text-center">Submit an answer to see evaluation</p>
      </Card>
    )
  }

  const scorePercentage = (evaluation.score / 10) * 100
  const scoreColor =
    evaluation.score >= 7 ? 'text-accent' : evaluation.score >= 5 ? 'text-warning' : 'text-error'

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="space-y-6">
        {/* Score Section */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Star className={`h-5 w-5 ${scoreColor}`} />
            <h3 className="font-semibold text-text">Performance Score</h3>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className={`text-3xl font-bold ${scoreColor}`}>{evaluation.score}</span>
              <span className="text-sm text-text-secondary">/10</span>
            </div>
            <div className="h-2 bg-surface-light rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${scorePercentage}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
                className={`h-full rounded-full ${scoreColor === 'text-accent' ? 'bg-accent' : scoreColor === 'text-warning' ? 'bg-warning' : 'bg-error'}`}
              />
            </div>
          </div>
        </div>

        {/* Feedback Section */}
        {evaluation.feedback && (
          <div className="space-y-2">
            <h4 className="font-semibold text-text">Feedback</h4>
            <p className="text-sm text-text-secondary leading-relaxed">{evaluation.feedback}</p>
          </div>
        )}

        {/* Strengths Section */}
        {evaluation.strengths.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-accent" />
              <h4 className="font-semibold text-text">Strengths</h4>
            </div>
            <ul className="space-y-2">
              {evaluation.strengths.map((strength, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-start gap-2 text-sm text-text-secondary"
                >
                  <span className="text-accent mt-1">•</span>
                  <span>{strength}</span>
                </motion.li>
              ))}
            </ul>
          </div>
        )}

        {/* Weaknesses Section */}
        {evaluation.weaknesses.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-warning" />
              <h4 className="font-semibold text-text">Areas to Improve</h4>
            </div>
            <ul className="space-y-2">
              {evaluation.weaknesses.map((weakness, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-start gap-2 text-sm text-text-secondary"
                >
                  <span className="text-warning mt-1">•</span>
                  <span>{weakness}</span>
                </motion.li>
              ))}
            </ul>
          </div>
        )}

        {/* Next Question Hint */}
        {evaluation.nextQuestion && (
          <div className="border-t border-surface-light pt-4">
            <div className="flex items-start gap-2 text-xs text-text-secondary">
              <TrendingUp className="h-4 w-4 flex-shrink-0 mt-0.5" />
              <span>Next question is loading...</span>
            </div>
          </div>
        )}
      </Card>
    </motion.div>
  )
}
