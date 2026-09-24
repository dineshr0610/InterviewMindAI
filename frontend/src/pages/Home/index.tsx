import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useState, useRef, ChangeEvent } from 'react'
import { Header } from '../../components/layout/Header'
import { Footer } from '../../components/layout/Footer'
import { Input } from '../../components/ui/Input'
import { JobRoleCombobox } from '../../components/ui/JobRoleCombobox'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { useInterviewContext } from '../../context/InterviewContext'
import { interviewService } from '../../services/interviewService'
import { Sparkles, Zap, Trophy, ArrowRight, FileText, Upload, X, Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'

interface FormData {
  name: string
  role: string
  topic?: string
  difficulty: 'Easy' | 'Medium' | 'Hard'
}

export default function HomePage() {
  const navigate = useNavigate()
  const { startInterview, isLoading, error } = useInterviewContext()
  const [submitError, setSubmitError] = useState<string | null>(null)

  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [resumeContext, setResumeContext] = useState<string | null>(null)
  const [resumeLoading, setResumeLoading] = useState(false)
  const [resumeError, setResumeError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    defaultValues: {
      name: '',
      role: '',
      topic: '',
      difficulty: 'Easy',
    },
  })

  const roleField = register('role', {
    required: 'Job role is required',
    minLength: {
      value: 2,
      message: 'Job role must be at least 2 characters',
    },
  })

  const handleResumeUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setResumeError(null)
    setResumeLoading(true)

    try {
      if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
        throw new Error('Please upload a valid PDF resume.')
      }

      if (file.size > 5 * 1024 * 1024) {
        throw new Error('The resume file is too large. Maximum size is 5 MB.')
      }

      const result = await interviewService.uploadResume(file)

      if (!result.resume_text) {
        throw new Error('Unable to read this resume. Please upload a text-based PDF.')
      }

      setResumeFile(file)
      setResumeContext(result.resume_text)
      setResumeError(null)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to upload resume'
      setResumeError(errorMsg)
      setResumeFile(null)
      setResumeContext(null)
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
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const onSubmit = async (data: FormData) => {
    try {
      setSubmitError(null)
      await startInterview(
        data.name,
        data.role,
        data.topic || undefined,
        data.difficulty,
        resumeContext || undefined,
        resumeFile?.name || undefined
      )
      navigate('/interview')
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
          className="max-w-6xl mx-auto space-y-12"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Hero Section */}
          <motion.section variants={itemVariants} className="text-center space-y-6 py-8">
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-text mb-4">
              Ace Your Interviews with <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">AI</span>
            </h2>
            <p className="text-lg md:text-xl text-text-secondary max-w-2xl mx-auto">
              Get real-time feedback on your interview responses. Practice with AI-powered questions and improve your performance.
            </p>
          </motion.section>

          <div className="grid md:grid-cols-2 gap-8 items-center">
            {/* Features */}
            <motion.section variants={itemVariants} className="space-y-4">
              <h3 className="text-2xl font-bold text-text mb-6">Why Choose InterviewMind AI?</h3>

              <motion.div variants={itemVariants} className="space-y-3">
                <Card className="flex items-start gap-4">
                  <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-primary/20">
                    <Sparkles className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-text mb-1">AI-Powered Evaluation</h4>
                    <p className="text-sm text-text-secondary">Get instant feedback on content, delivery, and improvements</p>
                  </div>
                </Card>

                <Card className="flex items-start gap-4">
                  <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-secondary/20">
                    <Zap className="h-6 w-6 text-secondary" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-text mb-1">Resume-Based Personalization</h4>
                    <p className="text-sm text-text-secondary">Upload your resume and get questions tuned to your experience</p>
                  </div>
                </Card>

                <Card className="flex items-start gap-4">
                  <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-accent/20">
                    <Trophy className="h-6 w-6 text-accent" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-text mb-1">Unlimited Questions</h4>
                    <p className="text-sm text-text-secondary">Continue answering until you choose to end the interview</p>
                  </div>
                </Card>
              </motion.div>
            </motion.section>

            {/* Form Section */}
            <motion.section variants={itemVariants}>
              <Card variant="elevated" className="space-y-6 p-8">
                <div>
                  <h3 className="text-2xl font-bold text-text mb-2">Start Your AI Interview</h3>
                  <p className="text-text-secondary">Enter your details to begin practicing</p>
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

                  <div className="w-full space-y-2">
                    <label className="block text-sm font-medium text-text">Interview Difficulty</label>
                    <select
                      {...register('difficulty')}
                      className="w-full px-4 py-2.5 rounded-lg bg-surface border-2 border-surface-light text-text placeholder-text-secondary transition-all duration-200 focus:outline-none focus:border-primary focus:bg-surface-light"
                    >
                      <option value="Easy">Adaptive AI (Easy start)</option>
                      <option value="Medium">Medium</option>
                      <option value="Hard">Hard</option>
                    </select>
                  </div>

                  {/* Resume Upload */}
                  <div className="w-full space-y-2">
                    <label className="block text-sm font-medium text-text">Resume (Optional)</label>

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
                            <span className="text-xs">Supported format: PDF</span>
                          </>
                        )}
                      </button>
                    ) : (
                      <motion.div
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center justify-between gap-3 p-4 rounded-lg bg-primary/10 border border-primary/30"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <FileText className="h-8 w-8 text-primary flex-shrink-0" />
                          <div className="min-w-0">
                            <p className="font-medium text-text truncate">{resumeFile.name}</p>
                            <p className="text-xs text-text-secondary">Resume-Based Interview</p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={handleRemoveResume}
                          className="p-2 rounded-lg text-text-secondary hover:text-error hover:bg-error/10 transition-colors"
                          aria-label="Remove resume"
                        >
                          <X className="h-5 w-5" />
                        </button>
                      </motion.div>
                    )}

                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,application/pdf"
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

                  <Button
                    type="submit"
                    variant="primary"
                    size="lg"
                    isLoading={isSubmitting || isLoading}
                    className="w-full group"
                  >
                    Start Interview
                    <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </form>

                <div className="border-t border-surface-light pt-4">
                  <p className="text-xs text-text-secondary text-center">
                    No account needed. Answer as many questions as you like, then end the interview to see your results.
                  </p>
                </div>
              </Card>
            </motion.section>
          </div>
        </motion.div>
      </main>

      <Footer />
    </div>
  )
}
