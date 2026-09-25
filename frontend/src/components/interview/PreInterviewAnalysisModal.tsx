import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Briefcase,
  Layers,
  ArrowRight,
  TrendingUp,
  FileText,
  Target,
  ShieldCheck,
} from 'lucide-react'
import { Button } from '../ui/Button'

export interface ScoreBreakdown {
  core_skills: number
  technical_concepts: number
  project_experience: number
  frameworks_tools: number
  relevant_experience: number
}

export interface MatchedArea {
  topic: string
  category: string
  confidence: number
  evidence?: string
  source?: string
}

export interface MissingArea {
  topic?: string
  category?: string
  importance?: string
}

export interface FeedbackData {
  summary: string
  strengths: string[]
  focus_areas: string[]
  resume_improvements: string[]
}

export interface Module1AnalysisResult {
  selected_role: string
  role_match_score: number
  score_breakdown: ScoreBreakdown
  matched_areas: MatchedArea[]
  partial_matches?: MatchedArea[]
  missing_areas: (string | MissingArea)[]
  unrelated_skills?: string[]
  feedback: FeedbackData
  interview_context: MatchedArea[]
}

interface PreInterviewAnalysisModalProps {
  isOpen: boolean
  onClose: () => void
  onProceed: () => void
  analysis: Module1AnalysisResult | null
  candidateName: string
  isLoading?: boolean
}

export const PreInterviewAnalysisModal: React.FC<PreInterviewAnalysisModalProps> = ({
  isOpen,
  onClose,
  onProceed,
  analysis,
  candidateName,
  isLoading,
}) => {
  if (!isOpen || !analysis) return null

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-emerald-400'
    if (score >= 50) return 'text-amber-400'
    return 'text-blue-400'
  }

  const getScoreBadge = (score: number) => {
    if (score >= 75) return { label: 'Strong Fit', bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' }
    if (score >= 50) return { label: 'Moderate Fit', bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30' }
    return { label: 'Foundational Fit', bg: 'bg-blue-500/10 text-blue-400 border-blue-500/30' }
  }

  const badge = getScoreBadge(analysis.role_match_score)

  const breakdownItems = [
    { label: 'Core Skills', value: analysis.score_breakdown?.core_skills ?? 0, icon: Target },
    { label: 'Technical Concepts', value: analysis.score_breakdown?.technical_concepts ?? 0, icon: Layers },
    { label: 'Project Experience', value: analysis.score_breakdown?.project_experience ?? 0, icon: Briefcase },
    { label: 'Frameworks & Tools', value: analysis.score_breakdown?.frameworks_tools ?? 0, icon: ShieldCheck },
    { label: 'Relevant Experience', value: analysis.score_breakdown?.relevant_experience ?? 0, icon: TrendingUp },
  ]

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          transition={{ duration: 0.2 }}
          className="relative w-full max-w-3xl max-h-[90vh] flex flex-col rounded-2xl bg-surface border border-surface-light shadow-2xl overflow-hidden my-auto"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-surface-light bg-surface-light/40">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/20 text-primary">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-text">Resume Analysis & Role Alignment</h3>
                <p className="text-xs text-text-secondary">
                  Candidate: <span className="font-semibold text-text">{candidateName}</span> • Role:{' '}
                  <span className="font-semibold text-primary">{analysis.selected_role}</span>
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-text-secondary hover:text-text hover:bg-surface-light transition-colors"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Top Score Banner */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-5 rounded-xl bg-gradient-to-br from-surface-light/80 to-surface-light/30 border border-surface-light">
              <div className="flex flex-col items-center justify-center sm:border-r border-surface-light/50 sm:pr-4">
                <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Role Match Score</span>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className={`text-4xl font-extrabold ${getScoreColor(analysis.role_match_score)}`}>
                    {analysis.role_match_score}
                  </span>
                  <span className="text-sm text-text-secondary">/ 100</span>
                </div>
                <span className={`mt-2 text-xs px-2.5 py-0.5 rounded-full border font-medium ${badge.bg}`}>
                  {badge.label}
                </span>
              </div>

              <div className="sm:col-span-2 space-y-2.5 pl-0 sm:pl-2">
                <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider block">
                  Deterministic Score Breakdown
                </span>
                <div className="space-y-2">
                  {breakdownItems.map((item) => (
                    <div key={item.label} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-text-secondary flex items-center gap-1.5">
                          <item.icon className="h-3.5 w-3.5 text-primary/70" />
                          {item.label}
                        </span>
                        <span className="font-semibold text-text">{item.value}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-surface-light rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${item.value}%` }}
                          transition={{ duration: 0.5, delay: 0.1 }}
                          className="h-full bg-primary rounded-full"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Matched Areas & Verified Evidence */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                <h4 className="text-sm font-bold text-text">
                  Demonstrated Competencies & Evidence ({analysis.matched_areas?.length || 0})
                </h4>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-48 overflow-y-auto pr-1">
                {analysis.matched_areas && analysis.matched_areas.length > 0 ? (
                  analysis.matched_areas.map((match, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-lg bg-surface-light/30 border border-surface-light/60 hover:border-primary/40 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-xs text-text">{match.topic}</span>
                        {match.source && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary/10 text-primary font-medium truncate max-w-[120px]">
                            {match.source}
                          </span>
                        )}
                      </div>
                      {match.evidence ? (
                        <p className="text-[11px] text-text-secondary line-clamp-2 italic">
                          &ldquo;{match.evidence}&rdquo;
                        </p>
                      ) : (
                        <p className="text-[11px] text-text-secondary">Extracted from resume profile</p>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-text-secondary col-span-2">No direct overlap areas identified.</p>
                )}
              </div>
            </div>

            {/* Missing Areas & Recommendations */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Missing Topics */}
              <div className="p-4 rounded-xl bg-surface-light/20 border border-surface-light space-y-2">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-amber-400" />
                  <h4 className="text-xs font-bold text-text uppercase tracking-wider">Recommended Skills to Brush Up</h4>
                </div>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {analysis.missing_areas && analysis.missing_areas.length > 0 ? (
                    analysis.missing_areas.slice(0, 8).map((m, idx) => {
                      const skillName = typeof m === 'string' ? m : m?.topic || String(m)
                      return (
                        <span
                          key={idx}
                          className="text-xs px-2.5 py-1 rounded-md bg-amber-500/15 text-amber-300 font-medium border border-amber-500/30"
                        >
                          {skillName}
                        </span>
                      )
                    })
                  ) : (
                    <span className="text-xs text-text-secondary">All primary core competencies matched.</span>
                  )}
                </div>
              </div>

              {/* Feedback Summary */}
              <div className="p-4 rounded-xl bg-surface-light/20 border border-surface-light space-y-2">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-primary" />
                  <h4 className="text-xs font-bold text-text uppercase tracking-wider">AI Interviewer Focus</h4>
                </div>
                <p className="text-xs text-text-secondary leading-relaxed">
                  {analysis.feedback?.summary ||
                    'Questions will initially probe your project implementations, then adaptively test core technical and system design principles.'}
                </p>
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-surface-light bg-surface-light/20">
            <button
              onClick={onClose}
              className="text-xs font-medium text-text-secondary hover:text-text transition-colors"
            >
              Back to Form
            </button>
            <Button
              variant="primary"
              size="md"
              onClick={onProceed}
              isLoading={isLoading}
              className="group gap-2"
            >
              Start AI Interview
              <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </Button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
export default PreInterviewAnalysisModal
