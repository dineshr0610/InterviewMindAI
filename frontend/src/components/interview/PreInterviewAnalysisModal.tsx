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
  analysis_source?: 'gemini' | 'hybrid' | 'deterministic'
  ai_analysis?: {
    summary?: string;
    ai_match_score?: number;
    ai_score_breakdown?: {
      core_requirements: number;
      supporting_requirements: number;
      technology_alignment: number;
      project_relevance: number;
      experience_relevance: number;
    };
    core_requirements?: {
      requirement: string;
      importance: string;
      status: string;
      evidence: string[];
      confidence: number;
    }[];
    supporting_requirements?: {
      requirement: string;
      importance: string;
      status: string;
      evidence: string[];
      confidence: number;
    }[];
    technology_matches?: {
      technology: string;
      status: string;
      evidence: string[];
      confidence: number;
    }[];
    strong_matches?: string[];
    partial_matches?: string[];
    missing_or_unverified?: string[];
    relevant_projects?: {
      project: string;
      relevance: string;
      evidence: string[];
    }[];
    skill_gaps?: string[];
    transferable_skills?: string[];
    interview_focus_areas?: string[];
  }
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
    if (score >= 25) return 'text-blue-400'
    return 'text-indigo-400'
  }

  const getRequirementBadge = (status: string) => {
    switch (status) {
      case 'strong_match': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
      case 'partial_match': return 'bg-amber-500/10 text-amber-400 border-amber-500/30'
      case 'missing_evidence':
      default: return 'bg-rose-500/10 text-rose-400 border-rose-500/30'
    }
  }

  const breakdownItems = [
    { label: 'Core Skills', value: analysis.score_breakdown?.core_skills ?? 0, icon: Target },
    { label: 'Technical Concepts', value: analysis.score_breakdown?.technical_concepts ?? 0, icon: Layers },
    { label: 'Project Experience', value: analysis.score_breakdown?.project_experience ?? 0, icon: Briefcase },
    { label: 'Frameworks & Tools', value: analysis.score_breakdown?.frameworks_tools ?? 0, icon: ShieldCheck },
    { label: 'Relevant Experience', value: analysis.score_breakdown?.relevant_experience ?? 0, icon: TrendingUp },
  ]

  const hasMatchedAreas = Boolean(analysis.matched_areas && analysis.matched_areas.length > 0)
  const isAiAvailable = analysis.analysis_source !== 'deterministic' && !!analysis.ai_analysis

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
                <p className="text-[10px] text-text-secondary mt-1">
                  Analysis Source:{' '}
                  <span className={`font-semibold ${isAiAvailable ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {isAiAvailable ? 'AI + Baseline matching' : 'Baseline matching only (AI unavailable)'}
                  </span>
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

            {/* Top Score Banner (Deterministic Baseline) */}
            <div className={`grid grid-cols-1 ${isAiAvailable && analysis.ai_analysis?.ai_match_score ? 'sm:grid-cols-4' : 'sm:grid-cols-3'} gap-4 p-5 rounded-xl bg-gradient-to-br from-surface-light/80 to-surface-light/30 border border-surface-light`}>
              <div className="flex flex-col items-center justify-center sm:border-r border-surface-light/50 sm:pr-4">
                <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider text-center">
                  BASELINE MATCH
                </span>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className={`text-4xl font-extrabold ${getScoreColor(analysis.role_match_score)}`}>
                    {analysis.role_match_score}
                  </span>
                  <span className="text-sm text-text-secondary">/ 100</span>
                </div>
                <p className="text-[9px] text-text-secondary/70 mt-2 text-center px-2">
                  Rule-based resume/role overlap.
                </p>
              </div>

              {isAiAvailable && (
                <div className="flex flex-col items-center justify-center sm:border-r border-surface-light/50 sm:px-4">
                  <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider text-center flex items-center gap-1">
                    <Sparkles className="w-3 h-3" /> AI MATCH
                  </span>
                  {analysis.ai_analysis?.ai_match_score !== undefined ? (
                    <>
                      <div className="flex items-baseline gap-1 mt-1">
                        <span className={`text-4xl font-extrabold text-emerald-400`}>
                          {analysis.ai_analysis.ai_match_score}
                        </span>
                        <span className="text-sm text-text-secondary">/ 100</span>
                      </div>
                      <p className="text-[9px] text-emerald-400/70 mt-2 text-center px-2">
                        Evidence-based assessment of candidate experience against the role requirements.
                      </p>
                    </>
                  ) : (
                    <p className="text-xs text-text-secondary mt-2">Unavailable</p>
                  )}
                </div>
              )}

              <div className={`sm:col-span-2 space-y-2.5 pl-0 ${isAiAvailable && analysis.ai_analysis?.ai_match_score ? 'sm:px-2' : 'sm:pl-2'}`}>
                <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider block">
                  Baseline Score Breakdown
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

            {/* AI Resume Analysis Section */}
            {!isAiAvailable ? (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
                <p className="text-sm font-semibold text-amber-400 mb-1">AI assessment unavailable</p>
                <p className="text-xs text-amber-200/80 leading-relaxed">
                  Only resume facts and baseline matching are shown below. No qualitative AI-generated conclusions or fit evaluations are displayed.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" />
                  <h4 className="text-sm font-bold text-text">AI Qualitative Assessment</h4>
                </div>
                <div className="space-y-4 p-4 rounded-xl bg-surface-light/20 border border-surface-light/60">
                  {analysis.ai_analysis!.summary && (
                    <div>
                      <h5 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1">Overall AI Summary</h5>
                      <p className="text-xs text-text leading-relaxed">{analysis.ai_analysis!.summary}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Core Requirements */}
                    {analysis.ai_analysis!.core_requirements && analysis.ai_analysis!.core_requirements.length > 0 && (
                      <div className="col-span-1 sm:col-span-2">
                        <h5 className="text-[10px] font-semibold text-primary uppercase tracking-wider mb-2">Core Requirements Evaluation</h5>
                        <div className="flex flex-col gap-2">
                          {analysis.ai_analysis!.core_requirements.map((req, idx) => (
                            <div key={idx} className={`px-3 py-2 rounded-lg border text-xs flex flex-col gap-1.5 ${getRequirementBadge(req.status)}`}>
                              <span className="font-bold flex justify-between">
                                <span>{req.requirement}</span>
                                <span className="opacity-80 font-semibold">
                                  {req.status === 'strong_match' ? 'Strong Match' : req.status === 'partial_match' ? 'Partial Match' : 'Missing Evidence'}
                                </span>
                              </span>
                              {req.evidence && req.evidence.length > 0 ? (
                                <div className="flex flex-col gap-0.5 mt-0.5">
                                  {req.evidence.map((ev: string, i: number) => (
                                    <span key={i} className="text-[10px] text-text-secondary/80 italic border-l-2 border-primary/20 pl-1.5">&ldquo;{ev}&rdquo;</span>
                                  ))}
                                </div>
                              ) : (
                                req.status === 'missing_evidence' && (
                                  <div className="text-[10px] text-text-secondary/80 italic mt-0.5">No explicit evidence found in resume.</div>
                                )
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Supporting Requirements */}
                    {analysis.ai_analysis!.supporting_requirements && analysis.ai_analysis!.supporting_requirements.length > 0 && (
                      <div className="col-span-1 sm:col-span-2">
                        <h5 className="text-[10px] font-semibold text-primary uppercase tracking-wider mb-2">Supporting Requirements</h5>
                        <div className="flex flex-col gap-2">
                          {analysis.ai_analysis!.supporting_requirements.map((req, idx) => (
                            <div key={idx} className={`px-3 py-2 rounded-lg border text-xs flex flex-col gap-1.5 ${getRequirementBadge(req.status)}`}>
                              <span className="font-bold flex justify-between">
                                <span>{req.requirement}</span>
                                <span className="opacity-80 font-semibold">
                                  {req.status === 'strong_match' ? 'Strong Match' : req.status === 'partial_match' ? 'Partial Match' : 'Missing Evidence'}
                                </span>
                              </span>
                              {req.evidence && req.evidence.length > 0 ? (
                                <div className="flex flex-col gap-0.5 mt-0.5">
                                  {req.evidence.map((ev: string, i: number) => (
                                    <span key={i} className="text-[10px] text-text-secondary/80 italic border-l-2 border-primary/20 pl-1.5">&ldquo;{ev}&rdquo;</span>
                                  ))}
                                </div>
                              ) : (
                                req.status === 'missing_evidence' && (
                                  <div className="text-[10px] text-text-secondary/80 italic mt-0.5">No explicit evidence found in resume.</div>
                                )
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Technology Stack Alignment */}
                    {analysis.ai_analysis!.technology_matches && analysis.ai_analysis!.technology_matches.length > 0 && (
                      <div className="col-span-1 sm:col-span-2 mt-1">
                        <h5 className="text-[10px] font-semibold text-primary uppercase tracking-wider mb-2">Technology Alignment</h5>
                        <div className="flex flex-wrap gap-2">
                          {analysis.ai_analysis!.technology_matches.map((tech, idx) => (
                            <div key={idx} className={`px-2 py-1 rounded border text-[11px] flex flex-col gap-1 ${getRequirementBadge(tech.status)}`}>
                              <span className="font-bold flex flex-col gap-0.5">
                                <span>{tech.technology}</span>
                                <span className="opacity-80 font-semibold text-[9px]">
                                  {tech.status === 'strong_match' ? 'Strong Match' : tech.status === 'partial_match' ? 'Partial Match' : 'Missing Evidence'}
                                </span>
                              </span>
                              {tech.evidence && tech.evidence.length > 0 ? (
                                <div className="flex flex-col gap-0.5">
                                  {tech.evidence.map((ev: string, i: number) => (
                                    <span key={i} className="text-[9px] text-text-secondary/80 italic border-l border-primary/20 pl-1 leading-tight max-w-[200px] line-clamp-2">&ldquo;{ev}&rdquo;</span>
                                  ))}
                                </div>
                              ) : (
                                tech.status === 'missing_evidence' && (
                                  <div className="text-[9px] text-text-secondary/80 italic mt-0.5">No explicit evidence found.</div>
                                )
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Advanced Fields */}
                    {analysis.ai_analysis!.relevant_projects && analysis.ai_analysis!.relevant_projects.length > 0 && (
                      <div className="col-span-1 sm:col-span-2 mt-2 space-y-2">
                        <h5 className="text-[10px] font-semibold text-blue-400 uppercase tracking-wider mb-1">Relevant Projects</h5>
                        {analysis.ai_analysis!.relevant_projects.map((proj, idx) => (
                          <div key={idx} className="p-3 rounded-lg bg-surface-light/30 border border-surface-light/60">
                            <h6 className="text-xs font-bold text-text mb-1">{proj.project}</h6>
                            {proj.relevance && (
                              <p className="text-[11px] text-text-secondary leading-relaxed mb-1.5">{proj.relevance}</p>
                            )}
                            {proj.evidence && proj.evidence.length > 0 && (
                              <div className="flex flex-col gap-0.5 mt-1">
                                {proj.evidence.map((ev: string, i: number) => (
                                  <span key={i} className="text-[10px] text-text-secondary/70 italic border-l-2 border-primary/30 pl-1.5">&ldquo;{ev}&rdquo;</span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {analysis.ai_analysis!.skill_gaps && analysis.ai_analysis!.skill_gaps.length > 0 && (
                      <div className="col-span-1 sm:col-span-2 mt-2">
                        <h5 className="text-[10px] font-semibold text-rose-400 uppercase tracking-wider mb-1">Skills / Technologies Not Evidenced</h5>
                        <ul className="list-disc list-inside text-xs text-text-secondary space-y-0.5">
                          {analysis.ai_analysis!.skill_gaps.map((item, idx) => <li key={idx}>{item}</li>)}
                        </ul>
                      </div>
                    )}

                    {analysis.ai_analysis!.transferable_skills && analysis.ai_analysis!.transferable_skills.length > 0 && (
                      <div className="col-span-1 sm:col-span-2 mt-2">
                        <h5 className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider mb-1">Transferable Skills</h5>
                        <ul className="list-disc list-inside text-xs text-text-secondary space-y-0.5">
                          {analysis.ai_analysis!.transferable_skills.map((item, idx) => <li key={idx}>{item}</li>)}
                        </ul>
                      </div>
                    )}

                    {analysis.ai_analysis!.interview_focus_areas && analysis.ai_analysis!.interview_focus_areas.length > 0 && (
                      <div className="col-span-1 sm:col-span-2 mt-2">
                        <h5 className="text-[10px] font-semibold text-primary uppercase tracking-wider mb-1">Interview Strategy & Focus</h5>
                        <ul className="list-disc list-inside text-xs text-text-secondary space-y-0.5">
                          {analysis.ai_analysis!.interview_focus_areas.map((item, idx) => <li key={idx}>{item}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Collapsible Baseline Details */}
            <details className="group space-y-4 border border-surface-light rounded-xl p-4 bg-surface/50">
              <summary className="text-xs font-bold text-text uppercase tracking-wider cursor-pointer list-none flex items-center justify-between">
                <span>Technical Baseline Details (Deterministic)</span>
                <span className="text-text-secondary group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="pt-4 space-y-6">
                {/* Keyword Extraction / Resume Facts Section */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    {hasMatchedAreas ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    ) : (
                      <Layers className="h-4 w-4 text-indigo-400" />
                    )}
                    <h4 className="text-sm font-bold text-text">
                      {hasMatchedAreas
                        ? `Role Keywords Found in Resume (${analysis.matched_areas.length})`
                        : `No Direct Keywords Found (0 Matches)`}
                    </h4>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-48 overflow-y-auto pr-1">
                    {hasMatchedAreas ? (
                      analysis.matched_areas.map((match, i) => (
                        <div
                          key={i}
                          className="p-3 rounded-lg bg-surface-light/30 border border-surface-light/60 transition-colors"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-xs text-text">{match.topic}</span>
                            {match.source && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-light text-text-secondary font-medium truncate max-w-[120px]">
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
                      <div className="col-span-2 p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30 space-y-2">
                        <p className="text-xs text-indigo-200 leading-relaxed font-medium">
                          Zero direct keyword matches were detected in this resume for <strong>{analysis.selected_role}</strong>.
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Baseline Missing Areas (Always shown) */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Missing Topics */}
                  <div className="p-4 rounded-xl bg-surface-light/20 border border-surface-light space-y-2">
                    <div className="flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-amber-400" />
                      <h4 className="text-xs font-bold text-text uppercase tracking-wider">Baseline Missing Keywords</h4>
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
                        <span className="text-xs text-text-secondary">All primary core keywords found.</span>
                      )}
                    </div>
                  </div>
                </div>

              </div>
            </details>
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
