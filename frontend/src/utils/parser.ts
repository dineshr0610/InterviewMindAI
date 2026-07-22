import { Evaluation } from '../types'

/**
 * Parse evaluation data (object or text blob) from backend
 */
export function parseEvaluation(input: any): Evaluation {
  if (typeof input === 'object' && input !== null) {
    const score = typeof input.score === 'number' ? input.score : 0
    const feedback = input.feedback || ''
    const strengths = Array.isArray(input.strengths)
      ? input.strengths
      : (typeof input.strengths === 'string' ? parseList(input.strengths) : [])
    const weaknesses = Array.isArray(input.improvements)
      ? input.improvements
      : (Array.isArray(input.weaknesses)
          ? input.weaknesses
          : (typeof input.improvements === 'string' ? parseList(input.improvements) : []))
    const nextQuestion = input.next_question || input.nextQuestion || ''

    return {
      score,
      feedback,
      strengths,
      weaknesses,
      nextQuestion,
      raw: JSON.stringify(input),
    }
  }

  const text = String(input || '')
  const evaluation: Evaluation = {
    score: 0,
    feedback: '',
    strengths: [],
    weaknesses: [],
    nextQuestion: '',
    raw: text,
  }

  try {
    // Extract score
    const scoreMatch = text.match(/Score:\s*(\d+)\s*\/\s*10/i)
    if (scoreMatch) {
      evaluation.score = parseInt(scoreMatch[1], 10)
    }

    // Extract feedback
    const feedbackMatch = text.match(/Feedback:\s*([\s\S]*?)(?=Strengths:|$)/i)
    if (feedbackMatch) {
      evaluation.feedback = feedbackMatch[1].trim()
    }

    // Extract strengths
    const strengthsMatch = text.match(/Strengths:\s*([\s\S]*?)(?=Weaknesses:|$)/i)
    if (strengthsMatch) {
      const strengthsText = strengthsMatch[1].trim()
      evaluation.strengths = parseList(strengthsText)
    }

    // Extract weaknesses
    const weaknessesMatch = text.match(/Weaknesses:\s*([\s\S]*?)(?=Next Question:|$)/i)
    if (weaknessesMatch) {
      const weaknessesText = weaknessesMatch[1].trim()
      evaluation.weaknesses = parseList(weaknessesText)
    }

    // Extract next question
    const nextQuestionMatch = text.match(/Next Question:\s*([\s\S]*?)$/i)
    if (nextQuestionMatch) {
      evaluation.nextQuestion = nextQuestionMatch[1].trim()
    }
  } catch (error) {
    console.error('[Parser] Error parsing evaluation:', error)
  }

  return evaluation
}

/**
 * Parse a list from text (handles bullet points, numbers, etc.)
 */
function parseList(text: string): string[] {
  const items = text
    .split(/[\n•\-\*]/)
    .map((item) => item.trim())
    .filter((item) => item.length > 0 && !item.match(/^\d+\.\s*$/) && item !== '*')
    .slice(0, 5) // Limit to 5 items

  return items
}
