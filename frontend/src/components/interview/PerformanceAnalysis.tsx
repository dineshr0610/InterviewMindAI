import { motion } from 'framer-motion'
import {
  Award,
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle,
  AlertCircle,
  Brain,
  Target,
} from 'lucide-react'
import { Card } from '../ui/Card'
import { ChatMessage } from '../../types'

interface PerformanceAnalysisProps {
  messages: ChatMessage[]
  candidateName: string
  role: string
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}

export function PerformanceAnalysis({
  messages,
  candidateName,
  role,
}: PerformanceAnalysisProps) {
  const evaluations = messages
    .filter((m) => m.type === 'evaluation' && m.evaluation)
    .map((m) => m.evaluation!)
  
  const answers = messages.filter((m) => m.type === 'answer')

  const scores = evaluations.map((e) => Number(e.score) || 0)

  const average =
    scores.length > 0
      ? scores.reduce((sum, score) => sum + score, 0) / scores.length
      : 0

  // Explainable scoring model:
  // 70% = average answer quality
  // 15% = consistency across answers
  // 15% = improvement trend
  const mean = average

  const variance =
    scores.length > 1
      ? scores.reduce((sum, score) => sum + Math.pow(score - mean, 2), 0) /
        scores.length
      : 0

  const standardDeviation = Math.sqrt(variance)

  const consistencyScore = clamp(
    10 - standardDeviation * 1.5,
    0,
    10
  )

  const firstScore = scores[0] || 0
  const lastScore = scores[scores.length - 1] || 0
  const trendDelta = lastScore - firstScore

  const trendScore = clamp(5 + trendDelta * 2.5, 0, 10)

  const finalScore =
    mean * 0.7 +
    consistencyScore * 0.15 +
    trendScore * 0.15

  const roundedFinal = Number(finalScore.toFixed(1))

  let recommendation = 'Needs Improvement'
  let recommendationText =
    'The candidate should strengthen core interview response quality before the next attempt.'

  if (roundedFinal >= 8.5) {
    recommendation = 'Strong Candidate'
    recommendationText =
      'Consistently strong responses with clear technical reasoning and strong interview readiness.'
  } else if (roundedFinal >= 7) {
    recommendation = 'Hire / Strong Potential'
    recommendationText =
      'Good overall performance with a solid technical foundation and manageable improvement areas.'
  } else if (roundedFinal >= 5.5) {
    recommendation = 'Borderline'
    recommendationText =
      'Shows useful knowledge, but response quality and consistency should improve.'
  }

  const strengths = Array.from(
    new Set(evaluations.flatMap((e) => e.strengths || []))
  ).slice(0, 5)

  const weaknesses = Array.from(
    new Set(evaluations.flatMap((e) => e.weaknesses || []))
  ).slice(0, 5)

  const TrendIcon =
    trendDelta > 0.25
      ? TrendingUp
      : trendDelta < -0.25
        ? TrendingDown
        : Minus

  const trendLabel =
    trendDelta > 0.25
      ? `Improved by ${trendDelta.toFixed(1)} points`
      : trendDelta < -0.25
        ? `Dropped by ${Math.abs(trendDelta).toFixed(1)} points`
        : 'Performance remained consistent'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <Card className="overflow-hidden">
        <div className="p-6 md:p-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 text-accent mb-2">
                <Award className="h-6 w-6" />
                <span className="font-semibold">Interview Complete</span>
              </div>

              <h1 className="text-2xl md:text-3xl font-bold text-text">
                Performance Analysis
              </h1>

              <p className="text-text-secondary mt-2">
                {candidateName} · {role}
              </p>
            </div>

            <div className="text-center">
              <div className="text-5xl font-bold text-accent">
                {roundedFinal}
              </div>
              <div className="text-sm text-text-secondary">/ 10</div>
              <div className="mt-2 font-semibold text-text">
                {recommendation}
              </div>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid md:grid-cols-3 gap-4">
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-3">
            <Brain className="h-5 w-5 text-accent" />
            <span className="font-semibold text-text">Answer Quality</span>
          </div>
          <div className="text-3xl font-bold text-text">
            {mean.toFixed(1)}/10
          </div>
          <p className="text-xs text-text-secondary mt-2">
            Average AI evaluation
          </p>
        </Card>

        <Card className="p-5">
          <div className="flex items-center gap-2 mb-3">
            <Target className="h-5 w-5 text-accent" />
            <span className="font-semibold text-text">Consistency</span>
          </div>
          <div className="text-3xl font-bold text-text">
            {consistencyScore.toFixed(1)}/10
          </div>
          <p className="text-xs text-text-secondary mt-2">
            Stability across answers
          </p>
        </Card>

        <Card className="p-5">
          <div className="flex items-center gap-2 mb-3">
            <TrendIcon className="h-5 w-5 text-accent" />
            <span className="font-semibold text-text">Progression</span>
          </div>
          <div className="text-lg font-bold text-text">
            {trendLabel}
          </div>
          <p className="text-xs text-text-secondary mt-2">
            Q1 compared with final response
          </p>
        </Card>
      </div>

      <Card className="p-6">
        <h2 className="text-lg font-bold text-text mb-2">
          Final Recommendation
        </h2>
        <p className="text-text-secondary leading-relaxed">
          {recommendationText}
        </p>
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="h-5 w-5 text-accent" />
            <h2 className="text-lg font-bold text-text">Key Strengths</h2>
          </div>

          {strengths.length > 0 ? (
            <ul className="space-y-3">
              {strengths.map((item, index) => (
                <motion.li
                  key={`${item}-${index}`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex gap-3 text-sm text-text-secondary"
                >
                  <span className="text-accent">✓</span>
                  <span>{item}</span>
                </motion.li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-text-secondary">
              No explicit strengths were returned by the evaluator.
            </p>
          )}
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertCircle className="h-5 w-5 text-warning" />
            <h2 className="text-lg font-bold text-text">
              Areas to Improve
            </h2>
          </div>

          {weaknesses.length > 0 ? (
            <ul className="space-y-3">
              {weaknesses.map((item, index) => (
                <motion.li
                  key={`${item}-${index}`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex gap-3 text-sm text-text-secondary"
                >
                  <span className="text-warning">•</span>
                  <span>{item}</span>
                </motion.li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-text-secondary">
              No major improvement areas were returned.
            </p>
          )}
        </Card>
      </div>

      <Card className="p-6">
        <h2 className="text-lg font-bold text-text mb-5">
          Question-by-Question Analysis
        </h2>

        <div className="space-y-4">
          {evaluations.map((evaluation, index) => (
            <div
              key={index}
              className="border border-surface-light rounded-lg p-4"
            >
              <div className="flex items-center justify-between gap-4 mb-2">
                <span className="font-semibold text-text">
                  Question {index + 1}
                </span>

                <span className="font-bold text-accent">
                  {evaluation.score}/10
                </span>
              </div>

              <p className="text-sm text-text-secondary leading-relaxed">
                {evaluation.feedback || 'Evaluation completed.'}
              </p>
            </div>
          ))}
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-lg font-bold text-text mb-3">
          How the Score Is Calculated
        </h2>

        <p className="text-sm text-text-secondary leading-relaxed">
          The demo uses an explainable three-factor model:
          <strong className="text-text"> 70%</strong> average AI answer quality,
          <strong className="text-text"> 15%</strong> consistency across answers,
          and <strong className="text-text"> 15%</strong> improvement trend.
          This makes the final score transparent and easy to explain during a
          review while still using the AI evaluator for the underlying answer
          assessment.
        </p>

        <p className="text-xs text-text-secondary mt-4">
          Completed responses: {answers.length} / {MAX_QUESTIONS_PLACEHOLDER}
        </p>
      </Card>
    </motion.div>
  )
}

const MAX_QUESTIONS_PLACEHOLDER = 3
