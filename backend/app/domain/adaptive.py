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
    has_resume = (
        resume_match.get("question_mode") in ("resume_grounded", "mixed")
        or bool(resume_match.get("resume_topics") or resume_match.get("matched_skills"))
    )
    topic_inventory = resume_match.get("topic_inventory") or {}
    evidence_items = resume_match.get("evidence_items") or topic_inventory.get("evidence_items") or []
    ai_focus_areas = list(resume_match.get("ai_focus_areas") or [])
    ai_skill_gaps = list(resume_match.get("ai_skill_gaps") or [])
    analysis_source = resume_match.get("analysis_source") or "deterministic"
    return {
        "phase": "technical",
        "interview_phase": "resume_phase" if has_resume else "role_phase",
        "current_topic": current_topic,
        "current_difficulty": difficulty or "Easy",
        "asked_questions": [],
        "asked_concepts": [],
        "topic_scores": {},
        "strengths": [],
        "weaknesses": [],
        "follow_up_depth": 0,
        "resume_questions_count": 0,
        "matched_resume_topics": resume_match.get("resume_topics") or resume_match.get("matched_skills") or [],
        "missing_skills": resume_match.get("missing_skills") or [],
        "ai_focus_areas": ai_focus_areas,
        "ai_skill_gaps": ai_skill_gaps,
        "analysis_source": analysis_source,
        "match_score": resume_match.get("match_score") or resume_match.get("resume_strength") or 0,
        "next_strategy": "baseline",
        "question_mode": resume_match.get("question_mode") or "foundational",
        "remaining_interview_time": None,
        "topic_inventory": topic_inventory,
        "evidence_items": evidence_items,
        "resume_evidence_used": [],
        "projects_covered": [],
        "technologies_covered": [],
        "categories_covered": [],
        "competencies_assessed": [],
        "sources_used": [],
        "question_intents_used": [],
        "recent_question_intents": [],
        "recent_question_topics": [current_topic],
        "strong_areas": [],
        "weak_areas": [],
        "misconceptions": [],
        "current_objective": "verify_resume_claims" if has_resume else "assess_role_competency",
        "topics_covered": [current_topic],
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
    matching = list(resume_match.get("matching_skills") or resume_match.get("matched_skills") or [])
    if not matching and resume_match.get("matched_areas"):
        for m in resume_match["matched_areas"]:
            area_name = m.get("area") or m.get("skill") or m.get("topic") if isinstance(m, dict) else str(m)
            if area_name and area_name not in matching:
                matching.append(area_name)

    if mode in ("resume_grounded", "mixed") and matching:
        for skill in matching:
            for topic in topics:
                if skill.lower() in topic.lower() or any(
                    token in topic.lower() for token in skill.lower().split() if len(token) > 3
                ):
                    return topic
        return matching[0]

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
    has_misconception = bool(missing_points)
    strategy = choose_next_strategy(technical_score, follow_up_depth, has_misconception=has_misconception)
    if strategy in DEEPENING_STRATEGIES:
        follow_up_depth += 1
    else:
        follow_up_depth = 0

    interview_phase = next_state.get("interview_phase", "role_phase")
    resume_questions_count = int(next_state.get("resume_questions_count") or 0)
    matched_resume_topics = list(next_state.get("matched_resume_topics") or [])
    missing_skills = list(next_state.get("missing_skills") or [])
    topic_inventory = dict(next_state.get("topic_inventory") or {})

    # Track strong and weak areas dynamically based on technical scores
    strong_areas = list(next_state.get("strong_areas") or [])
    weak_areas = list(next_state.get("weak_areas") or [])
    misconceptions = list(next_state.get("misconceptions") or [])

    if technical_score >= 8 and current_topic not in strong_areas:
        strong_areas.append(current_topic)
    elif technical_score <= 4 and current_topic not in weak_areas:
        weak_areas.append(current_topic)

    if missing_points:
        for mp in missing_points:
            if mp not in misconceptions:
                misconceptions.append(mp)

    if interview_phase == "resume_phase":
        resume_questions_count += 1
        all_resume_items = (
            matched_resume_topics
            + [p.get("name") for p in topic_inventory.get("projects") or [] if isinstance(p, dict)]
            + (topic_inventory.get("technologies") or [])
        )
        topics_covered = list(next_state.get("topics_covered") or [])
        unexplored_resume = [item for item in all_resume_items if item and item not in topics_covered]

        if not unexplored_resume and resume_questions_count >= len(matched_resume_topics) and resume_questions_count >= 6:
            interview_phase = "role_phase"

    # Select next topic dynamically based on inventory and strategy
    next_topic = choose_next_topic(
        role=role,
        current_topic=current_topic,
        topic_scores=topic_scores,
        technical_score=technical_score,
        strategy=strategy,
        missing_points=missing_points,
        topic_inventory=topic_inventory,
        matched_resume_topics=matched_resume_topics,
        missing_skills=missing_skills,
        topics_covered=list(next_state.get("topics_covered") or []),
        ai_focus_areas=list(next_state.get("ai_focus_areas") or []),
        ai_skill_gaps=list(next_state.get("ai_skill_gaps") or []),
    )

    updated_topics_covered = list(dict.fromkeys([*(next_state.get("topics_covered") or []), next_topic]))
    recent_topics = [*(next_state.get("recent_question_topics") or []), next_topic][-3:]

    # Dynamic objective determination
    if interview_phase == "resume_phase":
        current_obj = "verify_resume_claims" if resume_questions_count < 3 else "assess_technical_depth"
    elif missing_skills and next_topic in missing_skills:
        current_obj = "identify_gaps"
    else:
        current_obj = "assess_role_competency"

    next_state.update(
        {
            "interview_phase": interview_phase,
            "resume_questions_count": resume_questions_count,
            "current_topic": next_topic,
            "current_difficulty": difficulty,
            "topic_scores": topic_scores,
            "follow_up_depth": follow_up_depth,
            "next_strategy": strategy,
            "strengths": _merge_unique(next_state.get("strengths") or [], strengths)[:12],
            "weaknesses": _merge_unique(next_state.get("weaknesses") or [], weaknesses + missing_points)[:12],
            "strong_areas": strong_areas[:10],
            "weak_areas": weak_areas[:10],
            "misconceptions": misconceptions[:10],
            "current_objective": current_obj,
            "last_concept": concept,
            "topics_covered": updated_topics_covered,
            "recent_question_topics": recent_topics,
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
    topic_inventory: Optional[Dict[str, Any]] = None,
    matched_resume_topics: Optional[List[str]] = None,
    missing_skills: Optional[List[str]] = None,
    topics_covered: Optional[List[str]] = None,
    ai_focus_areas: Optional[List[str]] = None,
    ai_skill_gaps: Optional[List[str]] = None,
) -> str:
    topics = list(role.get("important_topics") or [])
    topic_inventory = topic_inventory or {}
    matched_resume_topics = matched_resume_topics or []
    missing_skills = missing_skills or []
    topics_covered = topics_covered or []
    ai_focus_areas = ai_focus_areas or []
    ai_skill_gaps = ai_skill_gaps or []

    # If the strategy is not topic_transition, stay on current topic
    if strategy != "topic_transition":
        return current_topic

    candidate_topics = {}

    # Gather potential topics and assign base scores
    projects = topic_inventory.get("projects") or []
    for proj in projects:
        proj_name = proj.get("name") if isinstance(proj, dict) else str(proj)
        if proj_name and proj_name not in topics_covered:
            candidate_topics[proj_name] = 8.0  # High priority for projects

    # AI-identified interview focus areas — probed with high priority (after projects)
    for focus in ai_focus_areas:
        if focus and focus not in topics_covered:
            candidate_topics[focus] = 7.5

    technologies = topic_inventory.get("technologies") or []
    for tech in technologies:
        if tech and tech not in topics_covered:
            candidate_topics[tech] = 7.0

    for r_topic in matched_resume_topics:
        if r_topic and r_topic not in topics_covered:
            candidate_topics[r_topic] = 6.0

    # AI-identified skill gaps — probe these to expose depth
    for gap in ai_skill_gaps:
        if gap and gap not in topics_covered:
            candidate_topics[gap] = 5.5

    for missing in missing_skills:
        if missing and missing not in topics_covered:
            candidate_topics[missing] = 5.0

    for role_topic in topics:
        if role_topic and role_topic not in topics_covered:
            candidate_topics[role_topic] = 4.0

    # Adjust scores based on candidate state
    weak_topics = [t for t, s in topic_scores.items() if s <= 5 and t != current_topic]
    for weak in weak_topics:
        # Re-visiting weak topics gets a medium priority, but lower than new resume topics
        candidate_topics[weak] = 5.5

    # If we have misconceptions, it might be worth diving into them as a topic
    if missing_points:
        mp_topic = f"{current_topic} concepts: {missing_points[0][:40]}"
        if mp_topic not in topics_covered:
            candidate_topics[mp_topic] = 6.5

    if not candidate_topics:
        return current_topic

    # Select the topic with the highest score
    best_topic = max(candidate_topics.items(), key=lambda x: x[1])[0]
    return best_topic


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
