"""Orchestration service for Module 1 (Resume Processing Module).

Coordinates parsing, normalization, technical extraction, role matching,
deterministic scoring, feedback generation, and Module 2 context construction.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from app.resume_processing.config import get_role_by_identifier, list_roles
from app.resume_processing.extractor import TechnicalExtractor, get_extractor
from app.resume_processing.feedback import FeedbackGenerator, get_feedback_generator
from app.resume_processing.matcher import RoleMatcher, get_matcher
from app.resume_processing.parser import ParsedResume, parse_resume_bytes, parse_resume_text
from app.resume_processing.schemas import (
    Feedback,
    InterviewContextItem,
    MatchedArea,
    Module1Output,
    ScoreBreakdown,
)
from app.resume_processing.scorer import DeterministicScorer, get_scorer

logger = logging.getLogger("interviewmind.resume_processing.service")


class ResumeProcessingService:
    """End-to-end processing service for Module 1."""

    def __init__(self) -> None:
        self.extractor: TechnicalExtractor = get_extractor()
        self.matcher: RoleMatcher = get_matcher()
        self.scorer: DeterministicScorer = get_scorer()
        self.feedback_generator: FeedbackGenerator = get_feedback_generator()

    def process(
        self,
        resume_data: Union[bytes, str, ParsedResume],
        role: str,
        filename: Optional[str] = None,
        candidate_name: Optional[str] = None,
    ) -> Module1Output:
        """
        Process a resume against a single selected role and return standard Module 1 output.
        """
        # Step 1: Parse resume into structured representation
        if isinstance(resume_data, bytes):
            parsed_resume = parse_resume_bytes(resume_data, filename=filename)
        elif isinstance(resume_data, str):
            parsed_resume = parse_resume_text(resume_data, filename=filename)
        elif isinstance(resume_data, ParsedResume):
            parsed_resume = resume_data
        else:
            raise ValueError("Unsupported resume data format. Expected bytes, str, or ParsedResume.")

        # Step 2: Technical information and evidence extraction
        profile = self.extractor.extract(parsed_resume, candidate_name=candidate_name)

        # Step 3: Match strictly against the single selected role
        match_result = self.matcher.match(profile, selected_role_identifier=role)

        # Step 4: Deterministic score calculation
        role_match_score, score_breakdown = self.scorer.compute_score(match_result)

        # Step 5: Actionable feedback generation
        feedback = self.feedback_generator.generate(match_result, role_match_score, score_breakdown)

        # Step 6: Construct structured interview_context for Module 2
        interview_context = self._build_interview_context(match_result)

        # Step 7: Assemble validated Module 1 output payload
        output = Module1Output(
            selected_role=match_result.selected_role,
            role_match_score=role_match_score,
            score_breakdown=score_breakdown,
            matched_areas=match_result.matched_areas,
            partial_matches=match_result.partial_matches,
            missing_areas=match_result.missing_areas,
            unrelated_skills=match_result.unrelated_skills,
            feedback=feedback,
            interview_context=interview_context,
        )

        logger.info(
            "Processed resume for role '%s': score=%.1f, matched=%d, interview_context=%d items",
            output.selected_role,
            output.role_match_score,
            len(output.matched_areas),
            len(output.interview_context),
        )

        return output

    def _build_interview_context(self, match_result) -> List[InterviewContextItem]:
        """
        Assemble the structured interview_context list for Module 2 question generation.
        Includes candidate's demonstrated topics, categories, confidence, sources, and evidence.
        Falls back to core role foundational topics if 0 direct matches are found.
        """
        context_items: List[InterviewContextItem] = []
        seen_topics = set()

        # Prioritize high-confidence matched areas with concrete evidence
        for match in match_result.matched_areas:
            if match.topic.lower() not in seen_topics:
                seen_topics.add(match.topic.lower())
                context_items.append(
                    InterviewContextItem(
                        topic=match.topic,
                        category=match.category,
                        confidence=match.confidence,
                        evidence=match.evidence,
                        source=match.source,
                    )
                )

        # If zero matches found: inject general foundational topics for the role
        if not context_items and match_result.role_profile:
            role_p = match_result.role_profile
            foundations = (
                role_p.core_skills[:3]
                + role_p.technical_concepts[:3]
                + role_p.programming_languages[:2]
            )
            for top in foundations:
                if top and top.lower() not in seen_topics:
                    seen_topics.add(top.lower())
                    context_items.append(
                        InterviewContextItem(
                            topic=top,
                            category="general_foundations",
                            confidence=0.5,
                            evidence=f"Core foundational competency for {role_p.role_name}",
                            source="General Role Foundations",
                        )
                    )

        return context_items

    @staticmethod
    def format_interview_context_for_prompt(
        interview_context: List[InterviewContextItem] | List[Dict[str, Any]],
        role_name: str,
    ) -> str:
        """
        Format structured interview context into a clear text prompt block for Module 2.
        Enables Module 2 to ground questions directly in candidate's project and experience evidence,
        or proceed with general foundational assessment if no direct overlap exists.
        """
        if not interview_context:
            return (
                f"FOUNDATIONAL ASSESSMENT MODE FOR {role_name.upper()}:\n"
                f"- Resume showed no direct skill matches for this specific role.\n"
                f"- Assess foundational principles, core theory, and standard coding problems in {role_name}."
            )

        is_all_foundational = True
        lines = [f"VERIFIED RESUME EVIDENCE & TOPICS FOR {role_name.upper()}:"]
        for item in interview_context:
            if isinstance(item, InterviewContextItem):
                topic = item.topic
                source = item.source
                evidence = item.evidence
            elif isinstance(item, dict):
                topic = item.get("topic", "")
                source = item.get("source", "")
                evidence = item.get("evidence", "")
            else:
                continue

            if source != "General Role Foundations":
                is_all_foundational = False

            lines.append(f"- Topic: {topic} | Context: {source}")
            lines.append(f"  Evidence: \"{evidence}\"")

        if is_all_foundational:
            lines.insert(
                1,
                "(Note: Foundational Mode Active — Assess general core competencies for this role)"
            )

        return "\n".join(lines)

    @staticmethod
    def list_available_roles() -> List[Dict[str, Any]]:
        """Return the dynamically loaded role catalog from technical_roles.json."""
        return list_roles()

    @staticmethod
    def resolve_role(role_identifier: str) -> Optional[Dict[str, Any]]:
        """Resolve role details dynamically from technical_roles.json."""
        return get_role_by_identifier(role_identifier)


# Global service instance
_service_instance: Optional[ResumeProcessingService] = None


def get_resume_processing_service() -> ResumeProcessingService:
    global _service_instance
    if _service_instance is None:
        _service_instance = ResumeProcessingService()
    return _service_instance
