"""Deterministic scoring engine for Module 1.

Calculates overall role match score and detailed category breakdowns strictly
using the formulas, weights, and thresholds defined in scoring_config.json.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.resume_processing.config import load_scoring_config
from app.resume_processing.matcher import MatchResult
from app.resume_processing.schemas import ScoreBreakdown

logger = logging.getLogger("interviewmind.resume_processing.scorer")


class DeterministicScorer:
    """Calculates deterministic numerical scores from match results."""

    def __init__(self) -> None:
        self.config = load_scoring_config()

    def compute_score(self, match_result: MatchResult) -> tuple[float, ScoreBreakdown]:
        weights = self.config.get("weights", {
            "core_skills": 0.35,
            "technical_concepts": 0.25,
            "project_experience": 0.20,
            "frameworks_tools": 0.10,
            "relevant_experience": 0.10,
        })

        score_range = self.config.get("score_range", {"min": 0, "max": 100})
        min_score = float(score_range.get("min", 0))
        max_score = float(score_range.get("max", 100))

        # 1. Core skills score
        core_score = self._calculate_core_skills_score(match_result)

        # 2. Technical concepts score
        concepts_score = self._calculate_technical_concepts_score(match_result)

        # 3. Project experience score
        project_score = self._calculate_project_experience_score(match_result)

        # 4. Frameworks and tools score
        tools_score = self._calculate_frameworks_tools_score(match_result)

        # 5. Relevant experience score
        experience_score = self._calculate_relevant_experience_score(match_result)

        # Weighted combination
        overall = (
            core_score * weights.get("core_skills", 0.35)
            + concepts_score * weights.get("technical_concepts", 0.25)
            + project_score * weights.get("project_experience", 0.20)
            + tools_score * weights.get("frameworks_tools", 0.10)
            + experience_score * weights.get("relevant_experience", 0.10)
        )

        overall_clamped = round(min(max_score, max(min_score, overall)), 1)

        breakdown = ScoreBreakdown(
            core_skills=round(core_score, 1),
            technical_concepts=round(concepts_score, 1),
            project_experience=round(project_score, 1),
            frameworks_tools=round(tools_score, 1),
            relevant_experience=round(experience_score, 1),
        )

        return overall_clamped, breakdown

    def _calculate_core_skills_score(self, match: MatchResult) -> float:
        total_core = match.role_profile.core_skills + match.role_profile.programming_languages
        if not total_core:
            return 80.0

        matched_core = match.category_matches.get("core_skills", []) + match.category_matches.get("programming_languages", [])
        if not matched_core:
            return 0.0

        # Sum of confidences / total core skills
        sum_conf = sum(m.confidence for m in matched_core)
        ratio = sum_conf / max(1, len(total_core))

        # Core skills bonus for multiple demonstrated project evidences
        project_ev_count = sum(1 for m in matched_core if m.section == "Projects")
        bonus = min(15.0, project_ev_count * 5.0)

        raw_score = (ratio * 85.0) + bonus
        return min(100.0, max(0.0, raw_score))

    def _calculate_technical_concepts_score(self, match: MatchResult) -> float:
        total_concepts = match.role_profile.technical_concepts
        if not total_concepts:
            return 80.0

        matched_concepts = match.category_matches.get("technical_concepts", [])
        if not matched_concepts:
            return 0.0

        sum_conf = sum(m.confidence for m in matched_concepts)
        ratio = sum_conf / max(1, len(total_concepts))

        raw_score = ratio * 100.0
        # If candidate has solid core concepts demonstrated
        if len(matched_concepts) >= 3:
            raw_score = max(raw_score, 70.0)

        return min(100.0, max(0.0, raw_score))

    def _calculate_project_experience_score(self, match: MatchResult) -> float:
        candidate = match.candidate_profile
        if not candidate or not candidate.projects:
            # Fallback based on project section evidence
            proj_ev_count = sum(1 for m in match.matched_areas if m.section == "Projects")
            if proj_ev_count >= 3:
                return 80.0
            if proj_ev_count >= 1:
                return 65.0
            return 30.0 if match.matched_areas else 0.0

        # Evaluate project relevance
        total_score = 0.0
        for proj in candidate.projects:
            proj_techs = set(proj.get("technologies", []))
            # Overlap with role
            overlap = [m for m in match.matched_areas if m.topic in proj_techs or m.source == proj.get("title")]
            if overlap:
                total_score += 40.0 + min(15.0, len(overlap) * 5.0)
            elif proj.get("bullet_points") or len(proj.get("description", "")) > 40:
                total_score += 20.0

        return min(100.0, max(0.0, total_score))

    def _calculate_frameworks_tools_score(self, match: MatchResult) -> float:
        total_tools = match.role_profile.frameworks_tools
        if not total_tools:
            return 80.0

        matched_tools = match.category_matches.get("frameworks_tools", [])
        if not matched_tools:
            return 0.0

        sum_conf = sum(m.confidence for m in matched_tools)
        ratio = sum_conf / max(1, len(total_tools))
        raw_score = ratio * 100.0

        if len(matched_tools) >= 2:
            raw_score = max(raw_score, 65.0)

        return min(100.0, max(0.0, raw_score))

    def _calculate_relevant_experience_score(self, match: MatchResult) -> float:
        candidate = match.candidate_profile
        if not candidate:
            return 0.0

        # Check for work experience items
        if candidate.experience:
            role_overlap_skills = {m.topic.lower() for m in match.matched_areas}
            exp_relevant_count = 0
            has_general_exp = False

            for exp in candidate.experience:
                exp_text = (exp.get("raw_text") or "").lower()
                exp_techs = {t.lower() for t in exp.get("technologies", [])}

                overlap = role_overlap_skills.intersection(exp_techs) or [
                    m for m in match.matched_areas if m.section == "Work Experience" or m.topic.lower() in exp_text
                ]
                if overlap:
                    exp_relevant_count += len(overlap)
                elif len(exp_text) > 30:
                    has_general_exp = True

            if exp_relevant_count >= 3:
                return 100.0
            if exp_relevant_count == 2:
                return 75.0
            if exp_relevant_count == 1:
                return 50.0
            return 20.0 if has_general_exp else 0.0

        # If no work experience listed, evaluate relevance from project-based role alignment
        proj_matches = [m for m in match.matched_areas if m.section == "Projects"]
        if len(proj_matches) >= 4:
            return 70.0
        if len(proj_matches) >= 2:
            return 45.0
        if len(proj_matches) == 1:
            return 25.0

        return 0.0


# Global scorer instance
_scorer_instance: Optional[DeterministicScorer] = None


def get_scorer() -> DeterministicScorer:
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = DeterministicScorer()
    return _scorer_instance
