"""Deterministic adaptive topic/difficulty decisions."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

DIFFICULTY_ORDER = ["Easy", "Medium", "Hard"]


def initial_assessment_state(
    role: Dict[str, Any],
    resume_match: Dict[str, Any],
    requested_topic: Optional[str],
    difficulty: str,
) -> Dict[str, Any]:
    current_topic = pick_baseline_topic(role, resume_match, requested_topic)
    return {
        "phase": "technical",
        "current_topic": current_topic,
        "current_difficulty": difficulty or "Easy",
        "asked_questions": [],
        "asked_concepts": [],
        "topic_scores": {},
        "strengths": [],
        "weaknesses": [],
        "follow_up_depth": 0,
        "next_strategy": "baseline",
        "question_mode": resume_match.get("question_mode") or "foundational",
        "remaining_interview_time": None,
    }


def pick_baseline_topic(
    role: Dict[str, Any],
    resume_match: Dict[str, Any],
    requested_topic: Optional[str],
) -> str:
    topics = list(role.get("important_topics") or [])
    requested = (requested_topic or "").strip()
    role_name = (role.get("selected_name") or role.get("name") or "").strip()

    if requested and requested.lower() not in {role_name.lower(), "general technical"}:
        if not _looks_like_job_title(requested):
            return requested

    mode = resume_match.get("question_mode")
    matching = resume_match.get("matching_skills") or []
    if mode == "resume_grounded" and matching:
        for skill in matching:
            for topic in topics:
                if skill.lower() in topic.lower() or any(
                    token in topic.lower() for token in skill.lower().split() if len(token) > 3
                ):
                    return topic
        return f"{matching[0]} in production systems"

    if topics:
        return topics[0]
    return "Data structures"


def adapt_after_answer(
    state: Dict[str, Any],
    role: Dict[str, Any],
    technical_score: int,
    current_topic: str,
    current_difficulty: str,
    concept: Optional[str],
    missing_points: List[str],
    strengths: List[str],
    weaknesses: List[str],
) -> Dict[str, Any]:
    from ai_engine.services.question_controller import (
        DEEPENING_STRATEGIES,
        choose_next_strategy,
    )

    next_state = dict(state or {})
    topic_scores = dict(next_state.get("topic_scores") or {})
    previous = topic_scores.get(current_topic)
    topic_scores[current_topic] = (
        technical_score if previous is None else round((previous + technical_score) / 2, 2)
    )

    difficulty = _adjust_difficulty(technical_score, current_difficulty)
    follow_up_depth = int(next_state.get("follow_up_depth") or 0)
    strategy = choose_next_strategy(technical_score, follow_up_depth)
    if strategy in DEEPENING_STRATEGIES:
        follow_up_depth += 1
    else:
        follow_up_depth = 0

    next_topic = choose_next_topic(
        role=role,
        current_topic=current_topic,
        topic_scores=topic_scores,
        technical_score=technical_score,
        strategy=strategy,
        missing_points=missing_points,
    )

    next_state.update(
        {
            "current_topic": next_topic,
            "current_difficulty": difficulty,
            "topic_scores": topic_scores,
            "follow_up_depth": follow_up_depth,
            "next_strategy": strategy,
            "strengths": _merge_unique(next_state.get("strengths") or [], strengths)[:12],
            "weaknesses": _merge_unique(next_state.get("weaknesses") or [], weaknesses + missing_points)[:12],
            "last_concept": concept,
        }
    )
    return next_state


def choose_next_topic(
    role: Dict[str, Any],
    current_topic: str,
    topic_scores: Dict[str, float],
    technical_score: int,
    strategy: str,
    missing_points: List[str],
) -> str:
    topics = list(role.get("important_topics") or [])
    if technical_score <= 4:
        return current_topic
    if strategy != "topic_transition" and technical_score < 8:
        return current_topic

    uncovered = [topic for topic in topics if topic not in topic_scores]
    weak = [
        topic
        for topic, score in topic_scores.items()
        if score <= 5 and topic != current_topic
    ]
    if uncovered:
        return uncovered[0]
    if weak:
        return weak[0]
    if missing_points:
        return f"{current_topic}: {missing_points[0][:80]}"
    return current_topic


def _adjust_difficulty(score: int, current: str) -> str:
    try:
        idx = DIFFICULTY_ORDER.index(current)
    except ValueError:
        idx = 0
    if score >= 8:
        idx = min(idx + 1, len(DIFFICULTY_ORDER) - 1)
    elif score <= 4:
        idx = max(idx - 1, 0)
    return DIFFICULTY_ORDER[idx]


def _merge_unique(existing: List[str], incoming: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in list(existing) + list(incoming):
        text = str(item).strip()
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _looks_like_job_title(value: str) -> bool:
    lowered = value.lower()
    return any(
        token in lowered
        for token in ("developer", "engineer", "scientist", "analyst", "manager", "designer")
    ) and " " in lowered.strip()
