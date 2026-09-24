"""Compare an extracted candidate profile with a technical role."""

from __future__ import annotations

from typing import Any, Dict, List


def match_resume_to_role(profile: Dict[str, Any], role: Dict[str, Any]) -> Dict[str, Any]:
    required = [str(item) for item in role.get("required_skills") or []]
    topics = [str(item) for item in role.get("important_topics") or []]
    candidate_terms = _terms(profile)

    matching_skills = [
        skill for skill in required if _contains_term(candidate_terms, skill)
    ]
    missing_skills = [skill for skill in required if skill not in matching_skills]
    relevant_technologies = [
        tech for tech in (profile.get("technologies") or [])
        if _contains_term(" ".join(required + topics).lower(), tech)
        or _contains_term(candidate_terms, tech)
    ]
    relevant_projects = [
        project for project in (profile.get("projects") or [])
        if _overlaps(project, required + topics)
    ]
    relevant_experience = [
        item for item in (profile.get("experience") or [])
        if _overlaps(item, required + topics)
    ]
    weak_areas = missing_skills[:6] or [
        topic for topic in topics if not _contains_term(candidate_terms, topic)
    ][:4]

    required_count = max(1, len(required)) if required else 1
    overlap_ratio = len(matching_skills) / required_count if required else (
        0.35 if profile.get("resume_present") else 0.0
    )
    bonus = min(0.2, 0.04 * len(relevant_projects) + 0.03 * len(relevant_experience))
    resume_strength = round(min(100.0, (overlap_ratio * 80.0) + (bonus * 100.0)))
    if not profile.get("resume_present"):
        resume_strength = 0.0
        role_relevance = "unknown"
        question_mode = "foundational"
    elif overlap_ratio >= 0.55 or relevant_projects:
        role_relevance = "strong"
        question_mode = "resume_grounded"
    elif overlap_ratio >= 0.25:
        role_relevance = "moderate"
        question_mode = "mixed"
    else:
        role_relevance = "weak"
        question_mode = "foundational"

    return {
        "role_id": role.get("id"),
        "role_name": role.get("selected_name") or role.get("name"),
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "relevant_technologies": relevant_technologies[:12],
        "relevant_projects": relevant_projects[:6],
        "relevant_experience": relevant_experience[:6],
        "weak_areas": weak_areas,
        "resume_strength": resume_strength,
        "role_relevance": role_relevance,
        "question_mode": question_mode,
        "overlap_ratio": round(overlap_ratio, 3),
    }


def _terms(profile: Dict[str, Any]) -> str:
    parts = []
    for key in ("skills", "technologies", "projects", "experience"):
        value = profile.get(key) or []
        parts.extend(str(item) for item in value)
    parts.append(str(profile.get("summary") or ""))
    return " ".join(parts).lower()


def _contains_term(haystack: str, term: str) -> bool:
    needle = (term or "").strip().lower()
    if not needle or not haystack:
        return False
    return needle in haystack or any(token and token in haystack for token in needle.split() if len(token) > 3)


def _overlaps(text: str, terms: List[str]) -> bool:
    blob = (text or "").lower()
    return any(_contains_term(blob, term) for term in terms)
