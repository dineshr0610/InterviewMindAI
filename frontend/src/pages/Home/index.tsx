import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useState } from 'react'
import { Header } from '../../components/layout/Header'
import { Footer } from '../../components/layout/Footer'
import { Input } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { useInterviewContext } from '../../context/InterviewContext'
import { Sparkles, Zap, Trophy, ArrowRight } from 'lucide-react'
import { motion } from 'framer-motion'

interface FormData {
  name: string
  role: string
}

export default function HomePage() {
  const navigate = useNavigate()
  const { startInterview, isLoading, error } = useInterviewContext()
  const [submitError, setSubmitError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    defaultValues: {
      name: '',
      role: '',
    },
  })

  const onSubmit = async (data: FormData) => {
    try {
      setSubmitError(null)
      await startInterview(data.name, data.role)
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
                    <h4 className="font-semibold text-text mb-1">Real-Time Feedback</h4>
                    <p className="text-sm text-text-secondary">Receive immediate insights after each answer</p>
                  </div>
                </Card>

                <Card className="flex items-start gap-4">
                  <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-accent/20">
                    <Trophy className="h-6 w-6 text-accent" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-text mb-1">Performance Metrics</h4>
                    <p className="text-sm text-text-secondary">Track scores, strengths, and areas for improvement</p>
                  </div>
                </Card>
              </motion.div>
            </motion.section>

            {/* Form Section */}
            <motion.section variants={itemVariants}>
              <Card variant="elevated" className="space-y-6 p-8">
                <div>
                  <h3 className="text-2xl font-bold text-text mb-2">Start Your Interview</h3>
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
                    label="Your Name"
                    placeholder="John Doe"
                    error={errors.name?.message}
                  />

                  <Input
                    {...register('role', {
                      required: 'Job role is required',
                      minLength: {
                        value: 2,
                        message: 'Job role must be at least 2 characters',
                      },
                    })}
                    label="Target Job Role"
                    placeholder="e.g., Senior Product Manager"
                    error={errors.role?.message}
                  />

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
                    No account needed. Your interview data is stored locally.
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
