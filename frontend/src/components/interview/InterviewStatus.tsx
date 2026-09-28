import { motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { QuestionTimer } from './QuestionTimer'
import { Button } from '../ui/Button'
import { LogOut, FileText } from 'lucide-react'

interface InterviewStatusProps {
  candidateName: string
  resumeUsed: boolean
  questionNumber: number
  totalQuestions: number | null
  startTime: number
  onEndInterview: () => void
  endDisabled: boolean
  difficulty?: string
}

export function InterviewStatus({
  candidateName,
  resumeUsed,
  questionNumber,
  totalQuestions,
  startTime,
  onEndInterview,
  endDisabled,
  difficulty = 'Easy',
}: InterviewStatusProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-5 flex flex-col gap-4 rounded-lg bg-surface/50 border border-surface-light p-4 lg:flex-row lg:items-center lg:justify-between"
    >
      <StatusItem
        label="Candidate"
        value={
          <span className="flex items-center gap-1.5 font-semibold text-text">
            {candidateName}
            {resumeUsed && (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                <FileText className="h-3 w-3" />
                Resume-Based
              </span>
            )}
          </span>
        }
      />

      <StatusItem
        label="Interview Type"
        value={resumeUsed ? 'Resume-Based' : 'Foundational'}
      />

      <StatusItem
        label="Adaptive AI Level"
        value={
          <span className="flex items-center gap-1.5 font-semibold">
            {difficulty === 'Hard' ? (
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2.5 py-0.5 rounded-full">
                <span className="h-1.5 w-1.5 rounded-full bg-rose-400 animate-pulse" />
                Hard (Advanced)
              </span>
            ) : difficulty === 'Medium' ? (
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-0.5 rounded-full">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
                Medium (Intermediate)
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Easy (Foundational)
              </span>
            )}
          </span>
        }
      />

      <StatusItem
        label="Question"
        value={
          totalQuestions && totalQuestions > 0
            ? `${questionNumber} / ${totalQuestions}`
            : String(questionNumber)
        }
      />

      <StatusItem label="Status" value={<LiveBadge />} />

      <div className="lg:order-last">
        <QuestionTimer startTime={startTime} />
      </div>

      <Button
        variant="outline"
        size="sm"
        onClick={onEndInterview}
        disabled={endDisabled}
      >
        <LogOut className="h-4 w-4" />
        End Interview
      </Button>
    </motion.div>
  )
}

function StatusItem({
  label,
  value,
}: {
  label: string
  value: ReactNode
}) {
  return (
    <div className="min-w-0">
      <p className="text-xs text-text-secondary">{label}</p>
      <div className="truncate">{value}</div>
    </div>
  )
}

function LiveBadge() {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="relative flex h-2.5 w-2.5">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-accent" />
      </span>
      <span className="font-semibold text-accent">Live</span>
    </span>
  )
}
