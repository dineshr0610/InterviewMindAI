import { useNavigate } from 'react-router-dom'
import { Button } from '../ui/Button'
import { Brain } from 'lucide-react'

interface HeaderProps {
  title?: string
  showHome?: boolean
}

export function Header({ title = 'InterviewMind AI', showHome = true }: HeaderProps) {
  const navigate = useNavigate()

  return (
    <header className="border-b border-surface-light bg-surface/80 backdrop-blur-sm sticky top-0 z-40">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/20">
            <Brain className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-text">{title}</h1>
            <p className="text-xs text-text-secondary">AI-Powered Interview Platform</p>
          </div>
        </div>
        {showHome && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/')}
          >
            Home
          </Button>
        )}
      </div>
    </header>
  )
}
