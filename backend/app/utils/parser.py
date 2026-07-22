"""
Utility for parsing AI evaluation text responses into structured data.
Matches the parser used in the frontend for consistent format.
"""

from __future__ import annotations

import re
from typing import Dict, List


def parse_evaluation(text: str) -> Dict:
    """
    Parse evaluation text from the AI engine into structured data.

    Expected format:
        Score: X/10
        Feedback: ...
        Strengths: ...
        Weaknesses/Improvements: ...
        Next Question: ...

    Args:
        text: Raw evaluation text from the AI engine.

    Returns:
        Dictionary with parsed score, feedback, strengths, improvements, and next_question.
    """
    evaluation: Dict = {
        "score": 0,
        "feedback": "",
        "strengths": [],
        "improvements": [],
        "next_question": "",
    }

    try:
        # Extract score
        score_match = re.search(r"Score:\s*(\d+)\s*/?\s*10", text, re.IGNORECASE)
        if score_match:
            evaluation["score"] = min(int(score_match.group(1), 10), 10)

        # Extract feedback
        feedback_match = re.search(
            r"Feedback:\s*([\s\S]*?)(?=Strengths:|Weaknesses:|Improvements:|Next Question:|$)",
            text,
            re.IGNORECASE,
        )
        if feedback_match:
            evaluation["feedback"] = feedback_match.group(1).strip()

        # Extract strengths (try both "Strengths:" and "Strengths:" patterns)
        strengths_match = re.search(
            r"Strengths:\s*([\s\S]*?)(?=Weaknesses:|Improvements:|Next Question:|$)",
            text,
            re.IGNORECASE,
        )
        if strengths_match:
            evaluation["strengths"] = _parse_list(strengths_match.group(1).strip())

        # Extract improvements (try "Weaknesses:" or "Improvements:" or "Areas to Improve:")
        improvements_match = re.search(
            r"(?:Weaknesses|Improvements|Areas to Improve):\s*([\s\S]*?)(?=Next Question:|$)",
            text,
            re.IGNORECASE,
        )
        if improvements_match:
            evaluation["improvements"] = _parse_list(improvements_match.group(1).strip())

        # Extract next question
        next_q_match = re.search(
            r"(?:Next Question|Next question):\s*([\s\S]*?)$",
            text,
            re.IGNORECASE,
        )
        if next_q_match:
            evaluation["next_question"] = next_q_match.group(1).strip()

    except Exception as exc:
        # If parsing fails, store the raw text in feedback
        evaluation["feedback"] = text
        pass

    return evaluation


def _parse_list(text: str) -> List[str]:
    """
    Parse a bulleted/numbered list from text.

    Handles:
        - Bullet points (•, -, *)
        - Numbered items (1., 2., etc.)
        - Newline-separated items

    Args:
        text: The text block containing list items.

    Returns:
        A list of extracted items, limited to 5 items maximum.
    """
    items = re.split(r"[\n•\-*]", text)
    cleaned = []
    for item in items:
        stripped = item.strip()
        # Remove numbered prefixes like "1. " or "1) "
        stripped = re.sub(r"^\d+[\.\)]\s*", "", stripped)
        if stripped and len(stripped) > 2:
            cleaned.append(stripped)

    return cleaned[:5]


def format_evaluation_for_response(evaluation: Dict) -> Dict:
    """
    Format parsed evaluation data into the standard API response format.

    Args:
        evaluation: The parsed evaluation dictionary.

    Returns:
        A formatted dictionary matching the AnswerResponse schema.
    """
    strengths = evaluation.get("strengths", [])
    improvements = evaluation.get("improvements", [])

    # Handle case where strengths/improvements come as comma-separated strings
    if isinstance(strengths, str):
        strengths = [s.strip() for s in strengths.split(",") if s.strip()]
    if isinstance(improvements, str):
        improvements = [s.strip() for s in improvements.split(",") if s.strip()]

    return {
        "score": evaluation.get("score", 0),
        "feedback": evaluation.get("feedback", ""),
        "strengths": strengths if isinstance(strengths, list) else [],
        "improvements": improvements if isinstance(improvements, list) else [],
        "next_question": evaluation.get("next_question", ""),
    }
