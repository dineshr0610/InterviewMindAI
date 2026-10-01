"""Question retrieval helpers: duplicates, similarity, RAG-aware prompts."""

from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence, Tuple


STOPWORDS = {
    "what", "when", "where", "which", "that", "this", "with", "from", "your",
    "about", "would", "could", "should", "into", "have", "been", "will",
    "them", "they", "their", "then", "than", "also", "just", "like", "make",
    "does", "doing", "explain", "describe", "please", "using", "used",
    "how", "why", "the", "and", "for", "are", "was", "you", "can", "a",
}


def question_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (text or "").lower())
        if token not in STOPWORDS and len(token) > 2
    }


def similarity(left: str, right: str) -> float:
    a = question_tokens(left)
    b = question_tokens(right)
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def is_duplicate(question: str, previous: Sequence[str], threshold: float = 0.72) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return True
    for previous_question in previous:
        p = (previous_question or "").strip().lower()
        if not p:
            continue
        if q == p:
            return True
        if similarity(q, p) >= threshold:
            return True
    return False


def select_non_duplicate(
    candidates: Iterable[str],
    previous: Sequence[str],
) -> Optional[str]:
    for candidate in candidates:
        text = (candidate or "").strip()
        if len(text) < 15:
            continue
        if not is_duplicate(text, previous):
            return text
    return None


def topic_aligned(question: str, topic: str, resume_context: Optional[str] = None) -> bool:
    topic_tokens = question_tokens(topic)
    if not topic_tokens:
        return True
    q_tokens = question_tokens(question)
    if bool(topic_tokens & q_tokens):
        return True
    if resume_context:
        resume_toks = question_tokens(resume_context)
        if len(q_tokens & resume_toks) >= 2:
            return True
    return False


def validate_question(
    question: str,
    topic: str,
    previous: Sequence[str],
    resume_context: Optional[str] = None,
) -> Tuple[bool, str]:
    text = (question or "").strip()
    if len(text) < 15:
        return False, "empty"
    if is_duplicate(text, previous):
        return False, "duplicate"
    if not topic_aligned(text, topic, resume_context=resume_context):
        return False, "topic_missing"
    lowered = text.lower()
    if re.fullmatch(r"what is .+[?]?$", lowered) and topic_aligned(topic, topic):
        generic = f"what is {topic.strip().lower()}"
        if lowered.startswith(generic) and _looks_like_job_title(topic):
            return False, "generic_role_question"
    return True, "valid"


def _looks_like_job_title(value: str) -> bool:
    lowered = value.lower()
    return any(
        token in lowered
        for token in ("developer", "engineer", "scientist", "analyst", "manager", "designer")
    )
