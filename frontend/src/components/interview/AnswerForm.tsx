import { useForm } from 'react-hook-form'
import { TextArea } from '../ui/TextArea'
import { Button } from '../ui/Button'
import { Send } from 'lucide-react'

interface AnswerFormProps {
  onSubmit: (answer: string) => Promise<void>
  isLoading: boolean
  disabled?: boolean
}

interface FormData {
  answer: string
}

export function AnswerForm({ onSubmit, isLoading, disabled }: AnswerFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      answer: '',
    },
  })

  const onFormSubmit = async (data: FormData) => {
    if (!data.answer.trim()) return

    try {
      await onSubmit(data.answer)
      reset()
    } catch (error) {
      console.error('[AnswerForm] Submission error:', error)
    }
  }

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
      <TextArea
        {...register('answer', {
          required: 'Please provide an answer',
          minLength: {
            value: 10,
            message: 'Answer must be at least 10 characters',
          },
        })}
        placeholder="Type your answer here..."
        error={errors.answer?.message}
        rows={4}
        disabled={isLoading || disabled}
        className="resize-none"
      />
      <Button
        type="submit"
        isLoading={isLoading}
        disabled={disabled}
        className="w-full"
      >
        <Send className="h-4 w-4" />
        Submit Answer
      </Button>
    </form>
  )
}
