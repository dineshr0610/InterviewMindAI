"""Final performance, skill-gap, recommendation, and progress analysis."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_final_assessment(
    *,
    candidate_name: str,
    role: Dict[str, Any],
    profile: Dict[str, Any],
    resume_match: Dict[str, Any],
    messages: List[Dict[str, Any]],
    coding: Optional[Dict[str, Any]] = None,
    previous: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    technical_scores = [
        _score(item.get("technical_score", item.get("score")))
        for item in messages
        if item.get("answer")
    ]
    communication_scores = [
        _score(item.get("communication_score"))
        for item in messages
        if item.get("answer") and item.get("communication_score") is not None
    ]
    technical_performance = _average(technical_scores)
    communication_performance = _average(communication_scores)
    coding_performance = None
    if coding:
        coding_performance = _score(coding.get("coding_score"))

    technical_strengths = _unique(
        [item for row in messages for item in _list(row.get("technical_strengths") or row.get("strengths"))]
    )
    technical_weaknesses = _unique(
        [item for row in messages for item in _list(row.get("technical_weaknesses") or row.get("improvements") or row.get("missing_points"))]
    )
    communication_strengths = _unique(
        [item for row in messages for item in _list(row.get("communication_strengths"))]
    )
    communication_weaknesses = _unique(
        [item for row in messages for item in _list(row.get("communication_improvements"))]
    )

    # Extract AI analysis enrichment from Module 1 output (if available)
    module1_output = resume_match.get("module1_output") or {}
    ai_analysis = module1_output.get("ai_analysis") or {}
    ai_focus_areas = ai_analysis.get("interview_focus_areas") or []
    ai_skill_gaps_raw = ai_analysis.get("skill_gaps") or []
    ai_transferable_skills = ai_analysis.get("transferable_skills") or []
    analysis_source = module1_output.get("analysis_source") or resume_match.get("analysis_source") or "deterministic"

    weak_topics = []
    topic_scores = {}
    for row in messages:
        topic = row.get("topic")
        score = _score(row.get("technical_score", row.get("score")))
        if topic and score is not None:
            topic_scores.setdefault(topic, []).append(score)
    for topic, scores in topic_scores.items():
        avg = _average(scores)
        if avg is not None and avg <= 5:
            weak_topics.append({"topic": topic, "score": avg})

    skill_gaps = detect_skill_gaps(
        role=role,
        resume_match=resume_match,
        weak_topics=weak_topics,
        technical_weaknesses=technical_weaknesses,
        coding=coding,
        communication_weaknesses=communication_weaknesses,
        ai_skill_gaps=ai_skill_gaps_raw,
        ai_focus_areas=ai_focus_areas,
    )
    recommendations = build_recommendations(skill_gaps, weak_topics, coding, resume_match)

    overall_parts = [part for part in [technical_performance, communication_performance] if part is not None]
    if coding_performance is not None:
        overall_parts.append(coding_performance)
    overall = _average(overall_parts)

    assessment = {
        "candidate_summary": _candidate_summary(candidate_name, role, profile, resume_match, technical_performance),
        "selected_role": role.get("selected_name") or role.get("name"),
        "role_id": role.get("id"),
        "resume_strength": resume_match.get("resume_strength"),
        "role_match": {
            "relevance": resume_match.get("role_relevance"),
            "matching_skills": resume_match.get("matching_skills") or [],
            "missing_skills": resume_match.get("missing_skills") or [],
        },
        "technical_performance": technical_performance,
        "communication_performance": communication_performance,
        "coding_performance": coding_performance,
        "strengths": {
            "technical": technical_strengths[:8],
            "communication": communication_strengths[:8],
            "coding": _coding_strengths(coding),
            "resume": resume_match.get("matching_skills") or [],
        },
        "weaknesses": {
            "technical": technical_weaknesses[:8],
            "communication": communication_weaknesses[:8],
            "coding": _coding_weaknesses(coding),
            "resume": resume_match.get("missing_skills") or [],
        },
        "skill_gaps": skill_gaps,
        "recommendations": recommendations,
        "topic_scores": {topic: _average(scores) for topic, scores in topic_scores.items()},
        "overall_assessment": overall,
        "questions_answered": len(technical_scores),
        # AI enrichment fields
        "analysis_source": analysis_source,
        "ai_interview_focus_areas": ai_focus_areas[:8],
        "ai_transferable_skills": ai_transferable_skills[:6],
    }
    if previous:
        assessment["progress_vs_previous"] = compare_assessments(previous, assessment)
    return assessment


def detect_skill_gaps(
    *,
    role: Dict[str, Any],
    resume_match: Dict[str, Any],
    weak_topics: List[Dict[str, Any]],
    technical_weaknesses: List[str],
    coding: Optional[Dict[str, Any]],
    communication_weaknesses: List[str],
    ai_skill_gaps: Optional[List[str]] = None,
    ai_focus_areas: Optional[List[str]] = None,
) -> Dict[str, Any]:
    missing_skills = list(resume_match.get("missing_skills") or [])
    weak_topic_names = [item["topic"] for item in weak_topics]
    coding_weaknesses = _coding_weaknesses(coding)
    covered = set(weak_topic_names)

    # Merge AI-identified skill gaps with deterministic missing skills.
    # AI gaps are additive; they never remove deterministic evidence.
    merged_ai_gaps = _unique((ai_skill_gaps or []) + missing_skills)[:12]

    return {
        "missing_skills": missing_skills,
        "weak_topics": weak_topic_names,
        "weak_concepts": technical_weaknesses[:8],
        "coding_weaknesses": coding_weaknesses,
        "communication_weaknesses": communication_weaknesses[:6],
        "ai_identified_gaps": (ai_skill_gaps or [])[:8],
        "ai_focus_areas_not_covered": [
            area for area in (ai_focus_areas or [])
            if area and area not in covered
        ][:6],
        "role_topics_not_covered": [
            topic
            for topic in (role.get("important_topics") or [])
            if topic not in covered
        ][:8],
    }


def build_recommendations(
    skill_gaps: Dict[str, Any],
    weak_topics: List[Dict[str, Any]],
    coding: Optional[Dict[str, Any]],
    resume_match: Dict[str, Any],
) -> Dict[str, List[str]]:
    technical_topics = [
        f"Revise {item['topic']} (scored {item['score']}/10 in this assessment)."
        for item in weak_topics
    ]
    for skill in (resume_match.get("missing_skills") or [])[:4]:
        technical_topics.append(f"Study {skill} because it is required for the selected role and was not evidenced on the resume.")
    for concept in (skill_gaps.get("weak_concepts") or [])[:4]:
        if len(concept) > 12:
            technical_topics.append(f"Practice explaining: {concept}")

    coding_areas: List[str] = []
    if coding:
        topic = coding.get("coding_topic") or coding.get("problem", {}).get("coding_topic")
        passed = coding.get("passed")
        total = coding.get("total")
        if total and passed is not None and passed < total:
            coding_areas.append(
                f"Practice {topic or 'the assigned coding topic'} until all public test cases pass "
                f"(passed {passed}/{total})."
            )
        if (coding.get("algorithm_quality") or 0) <= 5:
            coding_areas.append("Rewrite the solution with a clearer time-complexity target, preferably a linear hash-map or two-pointer approach where applicable.")

    communication = list(skill_gaps.get("communication_weaknesses") or [])
    resume_areas = [
        f"Add concrete evidence of {skill} to the resume (projects or quantified outcomes)."
        for skill in (resume_match.get("missing_skills") or [])[:5]
    ]

    priorities = technical_topics[:3] + coding_areas[:2] + communication[:1] + resume_areas[:1]
    return {
        "technical_topics": _unique(technical_topics)[:8] or ["No technical weakness was measured in this attempt."],
        "coding_practice_areas": _unique(coding_areas)[:6] or (
            ["Complete a role-specific coding problem to generate coding recommendations."]
            if not coding
            else ["No coding weakness was measured beyond the submitted problem."]
        ),
        "communication_improvements": _unique(communication)[:6] or ["No communication weakness was measured from the responses."],
        "resume_improvement_areas": _unique(resume_areas)[:6] or ["No resume gap was identified against the selected role."],
        "practice_priorities": _unique(priorities)[:8],
    }


def compare_assessments(previous: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    def delta(key: str) -> Optional[float]:
        before = previous.get(key)
        after = current.get(key)
        if before is None or after is None:
            return None
        try:
            return round(float(after) - float(before), 2)
        except (TypeError, ValueError):
            return None

    prev_topics = set((previous.get("topic_scores") or {}).keys())
    curr_topics = current.get("topic_scores") or {}
    improved = []
    remaining = []
    for topic, score in curr_topics.items():
        prev_score = (previous.get("topic_scores") or {}).get(topic)
        if prev_score is not None and score is not None and score > prev_score:
            improved.append(topic)
        if score is not None and score <= 5:
            remaining.append(topic)

    prev_gaps = set((previous.get("skill_gaps") or {}).get("missing_skills") or [])
    curr_gaps = set((current.get("skill_gaps") or {}).get("missing_skills") or [])
    return {
        "technical_score_change": delta("technical_performance"),
        "communication_score_change": delta("communication_performance"),
        "coding_score_change": delta("coding_performance"),
        "resume_strength_change": delta("resume_strength"),
        "improved_topics": improved,
        "remaining_weak_topics": remaining,
        "skill_gaps_resolved": sorted(prev_gaps - curr_gaps),
        "skill_gaps_remaining": sorted(curr_gaps),
        "previous_interview_id": previous.get("interview_id"),
    }


def _candidate_summary(
    name: str,
    role: Dict[str, Any],
    profile: Dict[str, Any],
    resume_match: Dict[str, Any],
    technical: Optional[float],
) -> str:
    skills = ", ".join((profile.get("skills") or [])[:6]) or "no extracted skills"
    tech = f"{technical}/10" if technical is not None else "n/a"
    return (
        f"{name} assessed for {role.get('selected_name') or role.get('name')}. "
        f"Resume strength {resume_match.get('resume_strength', 0)}/100 "
        f"({resume_match.get('role_relevance', 'unknown')} role overlap). "
        f"Extracted skills: {skills}. Technical performance: {tech}."
    )


def _coding_strengths(coding: Optional[Dict[str, Any]]) -> List[str]:
    if not coding:
        return []
    items = []
    if coding.get("passed") and coding.get("total") and coding["passed"] == coding["total"]:
        items.append("All executed test cases passed.")
    if (coding.get("algorithm_quality") or 0) >= 7:
        items.append("Algorithm choice appears appropriate for the problem.")
    return items


def _coding_weaknesses(coding: Optional[Dict[str, Any]]) -> List[str]:
    if not coding:
        return []
    items = []
    if coding.get("compile_error"):
        items.append(f"Compilation/load error: {coding['compile_error']}")
    if coding.get("runtime_error"):
        items.append(f"Runtime error: {coding['runtime_error']}")
    if coding.get("total") and coding.get("failed"):
        items.append(f"{coding['failed']} of {coding['total']} test cases failed.")
    if (coding.get("algorithm_quality") or 10) <= 5:
        items.append("Algorithm quality was weak on the submitted solution.")
    return items


def _score(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number > 10:
        number = number / 10.0
    return round(max(0.0, min(10.0, number)), 2)


def _average(values: List[Optional[float]]) -> Optional[float]:
    present = [float(v) for v in values if v is not None]
    if not present:
        return None
    return round(sum(present) / len(present), 2)


def _list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _unique(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        key = item.lower()
        if not item or key in seen:
            continue
        if item.lower() in {"practice more.", "improve your technical skills.", "good answer."}:
            continue
        seen.add(key)
        result.append(item)
    return result
