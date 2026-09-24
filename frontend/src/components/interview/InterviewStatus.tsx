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
}

export function InterviewStatus({
  candidateName,
  resumeUsed,
  questionNumber,
  totalQuestions,
  startTime,
  onEndInterview,
  endDisabled,
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
        value={resumeUsed ? 'Resume-Based' : 'General'}
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
