import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useState, useRef, useEffect, ChangeEvent } from 'react'
import { Header } from '../../components/layout/Header'
import { Footer } from '../../components/layout/Footer'
import { Input } from '../../components/ui/Input'
import { JobRoleCombobox } from '../../components/ui/JobRoleCombobox'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { useInterviewContext } from '../../context/InterviewContext'
import { interviewService } from '../../services/interviewService'
import { Sparkles, ArrowRight, FileText, Upload, X, Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'

import { PreInterviewAnalysisModal, Module1AnalysisResult } from '../../components/interview/PreInterviewAnalysisModal'

interface FormData {
  name: string
  role: string
  topic: string
}

export default function HomePage() {
  const navigate = useNavigate()
  const { startInterview, isLoading, error } = useInterviewContext()
  const [submitError, setSubmitError] = useState<string | null>(null)

  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [resumeContext, setResumeContext] = useState<string | null>(null)
  const [resumeLoading, setResumeLoading] = useState(false)
  const [resumeError, setResumeError] = useState<string | null>(null)
  const [analysisResult, setAnalysisResult] = useState<Module1AnalysisResult | null>(null)
  const [showAnalysisModal, setShowAnalysisModal] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    defaultValues: {
      name: '',
      role: '',
      topic: '',
    },
  })

  const selectedRole = watch('role')

  const roleField = register('role', {
    required: 'Job role is required',
    minLength: {
      value: 2,
      message: 'Job role must be at least 2 characters',
    },
  })

  const fetchResumeAnalysis = async (text: string, targetRole: string, candidateName: string) => {
    if (!text || !targetRole) return null
    try {
      setIsAnalyzing(true)
      const res = await interviewService.analyzeResume(text, targetRole, candidateName)
      const data = res.data || res
      setAnalysisResult(data)
      return data
    } catch (err) {
      console.warn('[Home] Resume analysis error:', err)
      return null
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Auto-analyze resume when target role changes
  useEffect(() => {
    if (resumeContext && selectedRole && selectedRole.trim().length >= 2) {
      fetchResumeAnalysis(resumeContext, selectedRole.trim(), getValues('name') || 'Candidate')
    }
  }, [selectedRole, resumeContext])

  const handleResumeUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setResumeError(null)
    setResumeLoading(true)

    try {
      const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
      const isDocx = file.name.toLowerCase().endsWith('.docx')

      if (!isPdf && !isDocx) {
        throw new Error('Please upload a valid PDF or DOCX resume.')
      }

      if (file.size > 5 * 1024 * 1024) {
        throw new Error('The resume file is too large. Maximum size is 5 MB.')
      }

      const currentRole = getValues('role')
      const result = await interviewService.uploadResume(file, currentRole || undefined)

      if (!result.resume_text) {
        throw new Error('Unable to read text from this resume.')
      }

      setResumeFile(file)
      setResumeContext(result.resume_text)
      setResumeError(null)

      if (currentRole && currentRole.trim()) {
        await fetchResumeAnalysis(result.resume_text, currentRole, getValues('name') || 'Candidate')
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to upload resume'
      setResumeError(errorMsg)
      setResumeFile(null)
      setResumeContext(null)
      setAnalysisResult(null)
    } finally {
      setResumeLoading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleRemoveResume = () => {
    setResumeFile(null)
    setResumeContext(null)
    setResumeError(null)
    setAnalysisResult(null)
    setShowAnalysisModal(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handlePreviewAnalysis = async () => {
    if (!resumeContext) return
    const currentRole = getValues('role')
    if (!currentRole || !currentRole.trim()) {
      setResumeError('Please select a Target Job Role to see role-specific match analysis.')
      return
    }

    if (!analysisResult) {
      const analysis = await fetchResumeAnalysis(
        resumeContext,
        currentRole,
        getValues('name') || 'Candidate'
      )
      if (analysis) {
        setShowAnalysisModal(true)
      }
    } else {
      setShowAnalysisModal(true)
    }
  }

  const proceedWithInterview = async () => {
    const data = getValues()
    try {
      setSubmitError(null)
      await startInterview(
        data.name,
        data.role,
        data.topic || undefined,
        'Easy',
        resumeContext || undefined,
        resumeFile?.name || undefined
      )
      setShowAnalysisModal(false)
      navigate('/interview')
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to start interview'
      setSubmitError(errorMsg)
      console.error('[Home] Interview start error:', err)
    }
  }

  const onSubmit = async (data: FormData) => {
    try {
      setSubmitError(null)

      // If a resume is uploaded, present the pre-interview analysis overview first!
      if (resumeContext && data.role) {
        let currentAnalysis = analysisResult
        if (!currentAnalysis || currentAnalysis.selected_role !== data.role) {
          currentAnalysis = await fetchResumeAnalysis(
            resumeContext,
            data.role,
            data.name || 'Candidate'
          )
        }
        if (currentAnalysis) {
          setShowAnalysisModal(true)
          return
        }
      }

      await proceedWithInterview()
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to start interview'
      setSubmitError(errorMsg)
      console.error('[Home] Interview start error:', err)
    }
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5 },
    },
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Header showHome={false} />

      <main className="flex-1 px-4 py-12 md:px-6 lg:px-8">
        <motion.div
          className="max-w-2xl mx-auto space-y-12"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Hero Section */}
          <motion.section variants={itemVariants} className="text-center space-y-4 py-8">
            <h2 className="text-4xl md:text-5xl font-bold text-text">
              Prepare for your interview
            </h2>
            <p className="text-lg text-text-secondary">
              Practice with questions tailored to your target role and experience.
            </p>
          </motion.section>

          <div className="flex justify-center items-center">
            {/* Form Section */}
            <motion.section variants={itemVariants} className="w-full">
              <Card variant="elevated" className="space-y-6 p-8">
                <div>
                  <h3 className="text-2xl font-bold text-text">Start Interview</h3>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                  <Input
                    {...register('name', {
                      required: 'Name is required',
                      minLength: {
                        value: 2,
                        message: 'Name must be at least 2 characters',
                      },
                    })}
                    label="Candidate Name"
                    placeholder="e.g., Alex Johnson"
                    error={errors.name?.message}
                  />

                  <JobRoleCombobox
                    label="Target Job Role"
                    name={roleField.name}
                    value={watch('role') || ''}
                    onChange={(value) => {
                      setValue('role', value.trim(), { shouldValidate: true })
                    }}
                    placeholder="Select a role or type your own"
                    error={errors.role?.message}
                  />

                  {/* Resume Upload */}
                  <div className="w-full space-y-2">
                    <div>
                      <label className="block text-sm font-medium text-text">Resume (Optional)</label>
                      <p className="text-sm text-text-secondary mt-1">Add your resume for questions tailored to your experience.</p>
                    </div>

                    {!resumeFile ? (
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={resumeLoading}
                        className="w-full flex flex-col items-center justify-center gap-2 p-6 rounded-lg border-2 border-dashed border-surface-light text-text-secondary hover:border-primary hover:bg-surface-light/50 transition-all duration-200"
                      >
                        {resumeLoading ? (
                          <>
                            <Loader2 className="h-8 w-8 text-primary animate-spin" />
                            <span className="text-sm">Processing resume...</span>
                          </>
                        ) : (
                          <>
                            <Upload className="h-8 w-8 text-primary" />
                            <span className="text-sm font-medium">Upload Resume</span>
                            <span className="text-xs">Supported format: PDF, DOCX</span>
                          </>
                        )}
                      </button>
                    ) : (
                      <motion.div
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-3.5 rounded-lg bg-primary/10 border border-primary/30 space-y-2.5"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-3 min-w-0">
                            <FileText className="h-8 w-8 text-primary flex-shrink-0" />
                            <div className="min-w-0">
                              <p className="font-medium text-text truncate text-sm">{resumeFile.name}</p>
                              <p className="text-xs text-text-secondary">
                                {analysisResult ? (
                                  <span className="text-primary font-semibold">
                                    Match: {analysisResult.role_match_score}/100 • {analysisResult.matched_areas?.length || 0} skills aligned{' '}
                                    {analysisResult.role_match_score === 0 || !analysisResult.matched_areas?.length
                                      ? '(Foundational Mode)'
                                      : ''}
                                  </span>
                                ) : isAnalyzing ? (
                                  'Analyzing role fit...'
                                ) : (
                                  'Resume uploaded'
                                )}
                              </p>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={handleRemoveResume}
                            className="p-1.5 rounded-lg text-text-secondary hover:text-error hover:bg-error/10 transition-colors"
                            aria-label="Remove resume"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>

                        {/* Preview Analysis Button */}
                        <div className="pt-1 border-t border-primary/20 flex items-center justify-between">
                          <button
                            type="button"
                            onClick={handlePreviewAnalysis}
                            disabled={isAnalyzing}
                            className="text-xs font-semibold text-primary hover:text-primary-light flex items-center gap-1.5 transition-colors"
                          >
                            <Sparkles className="h-3.5 w-3.5" />
                            {analysisResult ? 'View Match Breakdown & Gaps' : 'Preview Match Analysis'}
                          </button>
                          {analysisResult && (
                            <span className="text-[11px] text-text-secondary">
                              Target: <strong className="text-text">{analysisResult.selected_role}</strong>
                            </span>
                          )}
                        </div>
                      </motion.div>
                    )}

                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                      onChange={handleResumeUpload}
                      className="hidden"
                    />

                    {resumeError && (
                      <p className="text-sm text-error" role="alert">{resumeError}</p>
                    )}
                  </div>

                  {submitError && (
                    <div className="p-3 rounded-lg bg-error/10 border border-error/20 text-error text-sm">
                      {submitError}
                    </div>
                  )}

                  {error && (
                    <div className="p-3 rounded-lg bg-error/10 border border-error/20 text-error text-sm">
                      {error}
                    </div>
                  )}

                  <div className="pt-2">
                    <p className="text-sm text-text-secondary text-center mb-4">
                      Your interview adapts to your answers and performance.
                    </p>
                    <Button
                      type="submit"
                      variant="primary"
                      size="lg"
                      isLoading={isSubmitting || isLoading || isAnalyzing}
                      className="w-full group"
                    >
                      Start Interview
                      <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </div>
                </form>

                <div className="pt-2">
                  <p className="text-xs text-text-secondary text-center">
                    No account required
                  </p>
                </div>
              </Card>
            </motion.section>
          </div>
        </motion.div>
      </main>

      {/* Pre-Interview Resume Match & Skill Gaps Modal */}
      <PreInterviewAnalysisModal
        isOpen={showAnalysisModal}
        onClose={() => setShowAnalysisModal(false)}
        onProceed={proceedWithInterview}
        analysis={analysisResult}
        candidateName={watch('name') || 'Candidate'}
        isLoading={isLoading}
      />

      <Footer />
    </div>
  )
}
