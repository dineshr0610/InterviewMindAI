"""Communication-confidence indicators from response text.

These scores are linguistic indicators only. They are not a claim about the
candidate's psychological confidence.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


FILLERS = {
    "um", "uh", "erm", "like", "basically", "actually", "sort of", "kind of",
    "you know", "i think", "maybe", "perhaps",
}

TECHNICAL_CUES = {
    "because", "therefore", "however", "trade-off", "complexity", "invariant",
    "throughput", "latency", "consistency", "index", "cache", "transaction",
    "algorithm", "complexity", "api", "schema", "query", "thread", "lock",
}


def analyze_communication(answer: str, question: str = "") -> Dict[str, Any]:
    text = (answer or "").strip()
    if not text:
        return {
            "communication_score": 0,
            "clarity": 0,
            "structure": 0,
            "fluency": 0,
            "technical_terminology": 0,
            "explanation_quality": 0,
            "hesitation_indicators": [],
            "strengths": [],
            "improvements": ["Provide a structured spoken or written explanation."],
            "explanation": "No response text was available to analyse communication.",
        }

    sentences = [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]
    words = re.findall(r"[a-zA-Z']+", text.lower())
    filler_hits = [word for word in FILLERS if word in text.lower()]
    term_hits = [cue for cue in TECHNICAL_CUES if cue in text.lower()]

    clarity = 8 if len(sentences) >= 2 else 5
    if len(text) < 40:
        clarity = 3
    structure = 8 if len(sentences) >= 3 else (6 if len(sentences) == 2 else 4)
    fluency = 9 - min(5, len(filler_hits) * 2)
    terminology = min(10, 4 + len(term_hits) * 2)
    explanation_quality = 7 if any(w in text.lower() for w in ("because", "for example", "such as")) else 5
    if question and question.split(" ")[0].lower() in {"how", "why"} and "because" not in text.lower():
        explanation_quality = max(3, explanation_quality - 2)

    score = int(round(
        (clarity * 0.25)
        + (structure * 0.2)
        + (fluency * 0.2)
        + (terminology * 0.15)
        + (explanation_quality * 0.2)
    ))
    score = max(0, min(10, score))

    strengths: List[str] = []
    improvements: List[str] = []
    if structure >= 7:
        strengths.append("The response is organised into multiple complete points.")
    else:
        improvements.append("Organise the answer as: definition, mechanism, then example.")
    if terminology >= 7:
        strengths.append("Used relevant technical terminology.")
    else:
        improvements.append("Use precise technical terms from the question instead of general language.")
    if filler_hits:
        improvements.append(
            f"Reduce hesitation fillers ({', '.join(filler_hits[:3])}) to improve fluency."
        )
    else:
        strengths.append("The wording is relatively direct, with few hesitation fillers.")
    if explanation_quality < 6:
        improvements.append("Add a causal explanation (why the approach works) and one concrete example.")

    explanation = (
        f"Communication-confidence indicators are based on the written/transcribed answer "
        f"({len(words)} words, {len(sentences)} sentence(s)). "
        f"This is not a psychological confidence diagnosis."
    )
    return {
        "communication_score": score,
        "clarity": clarity,
        "structure": structure,
        "fluency": max(0, fluency),
        "technical_terminology": terminology,
        "explanation_quality": explanation_quality,
        "hesitation_indicators": filler_hits,
        "strengths": strengths[:4],
        "improvements": improvements[:4],
        "explanation": explanation,
    }
