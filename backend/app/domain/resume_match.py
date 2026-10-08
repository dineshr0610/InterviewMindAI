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
    has_any_match = bool(matching_skills or relevant_projects or relevant_technologies)
    if not profile.get("resume_present"):
        resume_strength = 0.0
        role_relevance = "unknown"
        question_mode = "foundational"
    elif not has_any_match:
        resume_strength = 0.0
        role_relevance = "zero_match"
        question_mode = "foundational"
    elif overlap_ratio >= 0.55 or len(relevant_projects) >= 2:
        role_relevance = "strong"
        question_mode = "resume_grounded"
    else:
        role_relevance = "moderate"
        question_mode = "mixed"

    # Build structured resume topics
    resume_topics: List[str] = []
    for skill in matching_skills:
        if skill not in resume_topics:
            resume_topics.append(skill)
    for tech in relevant_technologies:
        if tech not in resume_topics:
            resume_topics.append(tech)
    for topic in topics:
        if _contains_term(candidate_terms, topic) and topic not in resume_topics:
            resume_topics.append(topic)

    # Collect concrete evidence snippets
    evidence: List[str] = []
    for proj in relevant_projects:
        evidence.append(f"Project evidence: {proj}")
    for exp in relevant_experience:
        evidence.append(f"Experience evidence: {exp}")

    # Build actionable feedback
    suitability = (
        "High match - Strong alignment with role core skills and project experience."
        if question_mode == "resume_grounded"
        else (
            "Moderate match - Demonstrates partial relevant skills; some role topics require assessment."
            if question_mode == "mixed"
            else "Foundational match - Limited direct role skill overlap detected; foundational assessment recommended."
        )
    )
    feedback = {
        "suitability": suitability,
        "strengths": matching_skills[:6] or ["Demonstrated technical background"],
        "missing_skills": missing_skills[:6],
        "relevant_projects": relevant_projects[:4],
        "resume_improvements": [
            f"Highlight practical experience with {s}" for s in missing_skills[:3]
        ] if missing_skills else ["Resume provides strong coverage of target role requirements."],
    }

    score_breakdown = {
        "core_skills": round(overlap_ratio * 100.0, 1),
        "project_experience": round(min(100.0, len(relevant_projects) * 35.0), 1),
        "relevant_experience": round(min(100.0, len(relevant_experience) * 30.0), 1),
        "technologies": round(min(100.0, len(relevant_technologies) * 20.0), 1),
    }

    role_name = role.get("selected_name") or role.get("name") or "Software Engineer"

    # Build structured Topic Inventory and Evidence Model
    raw_projects = profile.get("projects") or []
    all_technologies = profile.get("technologies") or []
    projects_inventory: List[Dict[str, Any]] = []
    evidence_items: List[Dict[str, Any]] = []

    # Keywords for detecting explicit project capabilities
    explicit_topic_keywords = {
        "database_design": ["database", "schema", "sql", "postgres", "mysql", "mongodb", "table", "query", "migration"],
        "api_design": ["api", "rest", "graphql", "endpoint", "crud", "route", "controller", "microservice"],
        "security_auth": ["auth", "authentication", "authorization", "jwt", "oauth", "token", "password", "security", "role-based", "rbac"],
        "performance_scalability": ["optimize", "optimizing", "scale", "scaling", "index", "indexing", "cache", "redis", "latency", "throughput", "high-performance"],
        "debugging_edge_cases": ["debug", "testing", "unit test", "integration test", "troubleshoot", "fix", "error handling"],
        "architecture": ["architect", "architecture", "system design", "microservices", "modular", "component structure"],
        "data_flow": ["data flow", "pipeline", "stream", "websocket", "state management", "redux", "event-driven"],
        "implementation": ["built", "developed", "implemented", "created", "engineered", "coded"],
    }

    all_possible_topics = [
        "architecture",
        "data_flow",
        "implementation",
        "database_design",
        "api_design",
        "security_auth",
        "debugging_edge_cases",
        "performance_scalability",
        "trade_offs",
    ]

    for proj in raw_projects:
        proj_str = str(proj).strip()
        if not proj_str:
            continue
        # Extract title line if multi-line
        first_line = proj_str.split("\n")[0].strip()
        p_name = first_line.split(" - ")[0].split(":")[0].strip() or proj_str[:50]
        proj_lower = proj_str.lower()
        
        # Match technologies mentioned explicitly in this project
        p_techs = [
            tech for tech in all_technologies
            if _contains_term(proj_lower, tech)
        ]
        
        # Classify explicit vs inferred vs possible topics for this specific project
        explicit_topics = []
        for top_name, kw_list in explicit_topic_keywords.items():
            if any(_contains_term(proj_lower, kw) for kw in kw_list):
                explicit_topics.append(top_name)

        inferred_topics = [t for t in ["architecture", "data_flow", "implementation"] if t not in explicit_topics]
        possible_topics = [t for t in all_possible_topics if t not in explicit_topics and t not in inferred_topics]

        # Record explicit evidence items for this project
        for tech in (p_techs or matching_skills[:3]):
            evidence_items.append({
                "source_text": proj_str,
                "project": p_name,
                "technology": tech,
                "skill": tech,
                "responsibility": f"Used {tech} in project {p_name}",
                "evidence_strength": "explicit" if _contains_term(proj_lower, tech) else "inferred",
                "related_role_competency": "project_implementation",
            })

        for exp_top in explicit_topics:
            evidence_items.append({
                "source_text": proj_str,
                "project": p_name,
                "technology": p_techs[0] if p_techs else None,
                "skill": exp_top,
                "responsibility": f"Demonstrated {exp_top} in {p_name}",
                "evidence_strength": "explicit",
                "related_role_competency": exp_top,
            })

        projects_inventory.append({
            "name": p_name,
            "technologies": p_techs or matching_skills[:3],
            "verified_technologies": p_techs,
            "evidence": proj_str,
            "explicit_topics": explicit_topics,
            "inferred_topics": inferred_topics,
            "possible_topics": possible_topics,
            "topics": all_possible_topics,  # Preserved for backward compatibility
        })

    # Record possible topics from role requirements not explicitly present in resume
    for missing in missing_skills:
        evidence_items.append({
            "source_text": "",
            "project": None,
            "technology": missing,
            "skill": missing,
            "responsibility": f"Role requirement not evidenced in candidate resume",
            "evidence_strength": "possible",
            "related_role_competency": missing,
        })

    topic_inventory = {
        "projects": projects_inventory,
        "skills": matching_skills,
        "technologies": relevant_technologies,
        "experience": relevant_experience,
        "role_topics": topics,
        "missing_skills": missing_skills,
        "evidence_items": evidence_items,
        "verified_claims": [e for e in evidence_items if e["evidence_strength"] in ("explicit", "inferred")],
        "possible_topics": [e for e in evidence_items if e["evidence_strength"] == "possible"],
    }

    return {
        "role": role_name,
        "role_id": role.get("id"),
        "role_name": role_name,
        "match_score": resume_strength,
        "matched_skills": matching_skills,
        "matching_skills": matching_skills,
        "matched_technologies": relevant_technologies[:12],
        "relevant_technologies": relevant_technologies[:12],
        "matched_projects": relevant_projects[:6],
        "relevant_projects": relevant_projects[:6],
        "matched_experience": relevant_experience[:6],
        "relevant_experience": relevant_experience[:6],
        "missing_skills": missing_skills,
        "resume_topics": resume_topics[:12],
        "evidence": evidence[:10],
        "evidence_items": evidence_items,
        "topic_inventory": topic_inventory,
        "weak_areas": weak_areas,
        "resume_strength": resume_strength,
        "role_relevance": role_relevance,
        "question_mode": question_mode,
        "overlap_ratio": round(overlap_ratio, 3),
        "feedback": feedback,
        "score_breakdown": score_breakdown,
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
