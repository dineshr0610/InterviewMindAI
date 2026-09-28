"""Structured technical evaluation with a non-generic fallback."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


GENERIC_FEEDBACK = {
    "good answer",
    "provided a response",
    "good depth of explanation",
    "solid response demonstrating core technical understanding.",
    "good effort.",
}


def normalize_technical_evaluation(
    raw: Any,
    question: str,
    answer: str,
    topic: Optional[str] = None,
) -> Dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    heuristic = heuristic_technical_evaluation(question, answer, topic)

    score = _coerce_score(data.get("technical_score", data.get("score")))
    if score is None:
        score = heuristic["technical_score"]

    correct = _as_list(data.get("correct_points")) or heuristic["correct_points"]
    missing = _as_list(data.get("missing_points")) or heuristic["missing_points"]
    incorrect = _as_list(data.get("incorrect_points")) or heuristic["incorrect_points"]
    strengths = _as_list(data.get("strengths")) or correct[:3]
    weaknesses = _as_list(data.get("weaknesses")) or missing[:3]
    explanation = str(data.get("explanation") or data.get("feedback") or "").strip()
    if not explanation or explanation.lower().strip() in GENERIC_FEEDBACK:
        explanation = heuristic["explanation"]

    example = str(data.get("example_answer") or data.get("stronger_example_answer") or "").strip()
    if not example:
        example = heuristic["example_answer"]

    return {
        "technical_score": score,
        "correct_points": correct[:6],
        "missing_points": missing[:6],
        "incorrect_points": incorrect[:6],
        "strengths": strengths[:5],
        "weaknesses": weaknesses[:5],
        "explanation": explanation,
        "example_answer": example,
        "conceptual_understanding": _coerce_score(data.get("conceptual_understanding")) or score,
        "technical_depth": _coerce_score(data.get("technical_depth")) or max(0, score - 1),
        "completeness": _coerce_score(data.get("completeness")) or max(0, score - (2 if missing else 0)),
        "reasoning": _coerce_score(data.get("reasoning")) or score,
    }


def heuristic_technical_evaluation(
    question: str,
    answer: str,
    topic: Optional[str] = None,
) -> Dict[str, Any]:
    answer_text = (answer or "").strip()
    question_text = (question or "").strip()
    q_terms = _content_terms(question_text)
    a_terms = _content_terms(answer_text)
    overlap = sorted(q_terms & a_terms)
    missing_terms = sorted(q_terms - a_terms)

    snippet = _snippet(answer_text)
    if not answer_text:
        score = 0
        correct: List[str] = []
        missing = ["No answer was provided."]
        incorrect = ["Empty response."]
        explanation = f"The candidate did not answer: {question_text}"
    else:
        coverage = len(overlap) / max(1, len(q_terms))
        length_factor = min(1.0, len(answer_text) / 280)
        score = int(round(min(10, max(1, (coverage * 7) + (length_factor * 3)))))
        correct = [
            f"Referenced '{term}' while discussing the question."
            for term in overlap[:4]
        ] or [
            f"Provided a response to the question about {topic or 'the topic'}: \"{snippet}\""
        ]
        missing = [
            f"Did not address '{term}', which the question asked about."
            for term in missing_terms[:4]
        ] or [
            f"The answer did not connect clearly to: {question_text[:160]}"
        ]
        incorrect = []
        if len(answer_text) < 40:
            incorrect.append("The answer is too brief to demonstrate technical depth.")
        explanation = (
            f"For the question \"{question_text[:180]}\", the candidate said \"{snippet}\". "
            f"Matched concepts: {', '.join(overlap[:5]) or 'none'}. "
            f"Unaddressed concepts: {', '.join(missing_terms[:5]) or 'none clearly missing'}."
        )

    example = (
        f"A stronger answer would define {topic or 'the concept'}, walk through the mechanism, "
        f"give one concrete example, and mention an edge case or limitation related to: {question_text[:120]}"
    )
    return {
        "technical_score": score,
        "correct_points": correct,
        "missing_points": missing,
        "incorrect_points": incorrect,
        "strengths": correct[:3],
        "weaknesses": missing[:3],
        "explanation": explanation,
        "example_answer": example,
    }


def compose_feedback(
    technical: Dict[str, Any],
    communication: Dict[str, Any],
) -> Dict[str, Any]:
    feedback = (
        f"{technical.get('explanation', '').strip()} "
        f"Communication-confidence indicator {communication.get('communication_score', 0)}/10: "
        f"{communication.get('explanation', '')}"
    ).strip()
    return {
        "what_was_correct": technical.get("correct_points") or [],
        "what_was_missing": technical.get("missing_points") or [],
        "what_was_incorrect": technical.get("incorrect_points") or [],
        "technical_improvement": (technical.get("weaknesses") or [technical.get("example_answer")])[:3],
        "communication_improvement": communication.get("improvements") or [],
        "stronger_example_answer": technical.get("example_answer") or "",
        "feedback": feedback,
    }


def _content_terms(text: str) -> set[str]:
    stop = {
        "what", "when", "where", "which", "that", "this", "with", "from", "your",
        "about", "would", "could", "should", "into", "have", "been", "will",
        "them", "they", "their", "then", "than", "also", "just", "like", "make",
        "does", "doing", "explain", "describe", "please", "using", "used",
        "how", "why", "the", "and", "for", "are", "was", "you", "can",
    }
    return {
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_+#.-]{2,}", (text or "").lower())
        if token not in stop
    }


def _snippet(text: str, limit: int = 160) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip() + "..."


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [part.strip() for part in re.split(r"[,;\n]", value) if part.strip()]
    return []


def _coerce_score(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number > 10:
        number = number / 10.0
    return max(0, min(10, int(round(number))))
