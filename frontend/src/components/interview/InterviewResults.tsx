import { Button } from '../ui/Button'
import type { InterviewHistory } from '../../types'

interface InterviewResultsProps {
  history: InterviewHistory
  onStartAgain: () => void
}

export function InterviewResults({ history, onStartAgain }: InterviewResultsProps) {
  const answered = history.messages.filter((message) => message.answer)
  const scores = answered.map((message) => message.score ?? 0)
  const average = scores.length ? scores.reduce((sum, score) => sum + score, 0) / scores.length : 0
  const finalScore = scores.length ? scores[scores.length - 1] : 0
  const strengths = answered.flatMap((message) => (message.strengths || '').split(',').map((item) => item.trim()).filter(Boolean))
  const improvements = answered.flatMap((message) => (message.improvements || '').split(',').map((item) => item.trim()).filter(Boolean))

  return (
    <main className="flex-1 px-4 py-8 md:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <section className="rounded-lg border border-surface-light bg-surface p-6">
          <p className="text-sm text-text-secondary">Interview status</p>
          <h2 className="text-3xl font-bold text-text capitalize">{history.status}</h2>
          <p className="mt-2 text-text-secondary">{history.candidate_name} · {history.role} · {history.topic}</p>
        </section>
        <section className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-surface-light bg-surface p-4"><p className="text-sm text-text-secondary">Questions answered</p><p className="text-2xl font-bold text-text">{answered.length}</p></div>
          <div className="rounded-lg border border-surface-light bg-surface p-4"><p className="text-sm text-text-secondary">Final score</p><p className="text-2xl font-bold text-text">{finalScore}/10</p></div>
          <div className="rounded-lg border border-surface-light bg-surface p-4"><p className="text-sm text-text-secondary">Average score</p><p className="text-2xl font-bold text-text">{average.toFixed(1)}/10</p></div>
        </section>
        <section className="grid gap-6 md:grid-cols-2">
          <div className="rounded-lg border border-surface-light bg-surface p-5"><h3 className="font-semibold text-text">Strengths</h3><ul className="mt-3 list-disc pl-5 text-text-secondary">{strengths.length ? strengths.map((item, index) => <li key={`${item}-${index}`}>{item}</li>) : <li>No strengths recorded.</li>}</ul></div>
          <div className="rounded-lg border border-surface-light bg-surface p-5"><h3 className="font-semibold text-text">Weak areas / improvements</h3><ul className="mt-3 list-disc pl-5 text-text-secondary">{improvements.length ? improvements.map((item, index) => <li key={`${item}-${index}`}>{item}</li>) : <li>No improvements recorded.</li>}</ul></div>
        </section>
        <section className="rounded-lg border border-surface-light bg-surface p-5"><h3 className="font-semibold text-text">Transcript</h3><div className="mt-4 space-y-4">{history.messages.map((message, index) => <article key={index} className="border-t border-surface-light pt-4"><p className="font-medium text-text">Q{index + 1}. {message.question}</p><p className="mt-2 text-text-secondary">{message.answer || 'Not answered'}</p>{message.feedback && <p className="mt-2 text-sm text-text-secondary">Feedback: {message.feedback}</p>}{message.score !== null && <p className="mt-1 text-sm text-text-secondary">Score: {message.score}/10</p>}</article>)}</div></section>
        <Button onClick={onStartAgain}>Start another interview</Button>
      </div>
    </main>
  )
}
