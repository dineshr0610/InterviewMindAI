import { AnimatePresence, motion } from 'framer-motion'
import { Button } from '../ui/Button'

interface EndInterviewDialogProps {
  open: boolean
  isLoading: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function EndInterviewDialog({
  open,
  isLoading,
  onConfirm,
  onCancel,
}: EndInterviewDialogProps) {
  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onCancel}
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-md rounded-lg border border-surface-light bg-surface p-6"
          >
            <h3 className="text-lg font-semibold text-text">End Interview?</h3>
            <p className="mt-2 text-sm text-text-secondary">
              Your current interview progress will be saved. You will be able to
              view your performance analysis.
            </p>

            <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <Button variant="outline" onClick={onCancel} disabled={isLoading}>
                Continue Interview
              </Button>
              <Button
                variant="primary"
                isLoading={isLoading}
                onClick={onConfirm}
              >
                End Interview
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
