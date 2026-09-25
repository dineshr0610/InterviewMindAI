"""Module 1 - Resume Processing Module.

Provides resume parsing (PDF/DOCX), canonical skill normalization,
technical evidence extraction, single-role matching, deterministic scoring,
feedback generation, and Module 2 context integration.
"""

from app.resume_processing.service import ResumeProcessingService, get_resume_processing_service
from app.resume_processing.schemas import (
    Feedback,
    InterviewContextItem,
    MatchedArea,
    Module1AnalysisRequest,
    Module1Output,
    ScoreBreakdown,
)
from app.resume_processing.config import (
    get_role_by_identifier,
    list_roles,
    load_scoring_config,
    load_skill_aliases,
    load_technical_roles,
)

__all__ = [
    "ResumeProcessingService",
    "get_resume_processing_service",
    "Module1Output",
    "Module1AnalysisRequest",
    "MatchedArea",
    "InterviewContextItem",
    "ScoreBreakdown",
    "Feedback",
    "load_technical_roles",
    "load_skill_aliases",
    "load_scoring_config",
    "list_roles",
    "get_role_by_identifier",
]
