"""Feedback and recommendation generator for Module 1.

Generates deterministic, actionable feedback (strengths, focus areas, resume improvements)
based on role match results and identified gaps.
"""

from __future__ import annotations

import logging
from typing import List

from app.resume_processing.matcher import MatchResult
from app.resume_processing.schemas import Feedback, ScoreBreakdown

logger = logging.getLogger("interviewmind.resume_processing.feedback")


class FeedbackGenerator:
    """Generates structured, actionable feedback from match results."""

    def generate(
        self,
        match: MatchResult,
        score: float,
        breakdown: ScoreBreakdown,
    ) -> Feedback:
        strengths = self._generate_strengths(match)
        focus_areas = self._generate_focus_areas(match)
        improvements = self._generate_resume_improvements(match, breakdown)

        return Feedback(
            strengths=strengths,
            focus_areas=focus_areas,
            resume_improvements=improvements,
        )

    def _generate_strengths(self, match: MatchResult) -> List[str]:
        strengths: List[str] = []

        # Find project-backed matches
        project_backed = [m for m in match.matched_areas if m.section == "Projects"]
        if project_backed:
            top_proj_topics = ", ".join(m.topic for m in project_backed[:3])
            best_source = project_backed[0].source
            strengths.append(
                f"Demonstrated practical implementation of {top_proj_topics} in project '{best_source}'."
            )

        # Highlight top matched core skills & languages
        core_and_langs = [
            m for m in match.matched_areas
            if m.category in ("core_skills", "programming_languages")
        ]
        if core_and_langs:
            skill_names = ", ".join(m.topic for m in core_and_langs[:4])
            strengths.append(
                f"Strong foundational alignment with {match.selected_role} competencies ({skill_names})."
            )

        # Highlight matched frameworks & tools
        tools = [m for m in match.matched_areas if m.category == "frameworks_tools"]
        if tools:
            tool_names = ", ".join(m.topic for m in tools[:4])
            strengths.append(f"Hands-on familiarity with relevant tools and libraries: {tool_names}.")

        if not strengths and match.matched_areas:
            matched_names = ", ".join(m.topic for m in match.matched_areas[:3])
            strengths.append(f"Demonstrated relevant technical skills: {matched_names}.")

        return strengths or ["Candidate resume demonstrates technical fundamentals."]

    def _generate_focus_areas(self, match: MatchResult) -> List[str]:
        focus_areas: List[str] = []

        # Check missing core skills
        missing_core = [
            s for s in match.missing_areas
            if s in match.role_profile.core_skills
        ]
        if missing_core:
            focus_areas.append(
                f"Core {match.selected_role} competencies to strengthen: {', '.join(missing_core[:3])}."
            )

        # Check missing technical concepts
        missing_concepts = [
            s for s in match.missing_areas
            if s in match.role_profile.technical_concepts
        ]
        if missing_concepts:
            focus_areas.append(
                f"Prepare for interview questions on key concepts: {', '.join(missing_concepts[:3])}."
            )

        # Check missing tools/frameworks
        missing_tools = [
            s for s in match.missing_areas
            if s in match.role_profile.frameworks_tools
        ]
        if missing_tools:
            focus_areas.append(
                f"Gain practical exposure to role tooling: {', '.join(missing_tools[:3])}."
            )

        return focus_areas or [f"Review advanced system design and architecture patterns for {match.selected_role}."]

    def _generate_resume_improvements(
        self,
        match: MatchResult,
        breakdown: ScoreBreakdown,
    ) -> List[str]:
        improvements: List[str] = []

        if breakdown.project_experience < 75:
            improvements.append(
                "Add detailed project bullet points highlighting architectural decisions, algorithms, and libraries used."
            )

        if breakdown.frameworks_tools < 70:
            improvements.append(
                f"Explicitly list production frameworks and developer tools relevant to {match.selected_role}."
            )

        improvements.append(
            "Quantify project achievements with metrics (e.g., performance benchmarks, latency reductions, test coverage)."
        )

        return improvements


# Global feedback generator
_feedback_instance: Optional[FeedbackGenerator] = None


def get_feedback_generator() -> FeedbackGenerator:
    global _feedback_instance
    if _feedback_instance is None:
        _feedback_instance = FeedbackGenerator()
    return _feedback_instance
