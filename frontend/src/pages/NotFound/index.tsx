import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { AlertCircle } from 'lucide-react'
import { motion } from 'framer-motion'

export default function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="text-center space-y-6"
      >
        <div className="flex justify-center">
          <AlertCircle className="h-16 w-16 text-warning" />
        </div>

        <h1 className="text-4xl font-bold text-text">Page Not Found</h1>
        <p className="text-lg text-text-secondary max-w-md">
          The page you&apos;re looking for doesn&apos;t exist. Let&apos;s get you back on track.
        </p>

        <Button
          variant="primary"
          size="lg"
          onClick={() => navigate('/')}
        >
          Return to Home
        </Button>
      </motion.div>
    </div>
  )
}
