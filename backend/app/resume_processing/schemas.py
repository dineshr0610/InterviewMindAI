"""Pydantic schemas for Module 1 contracts adhering strictly to module1_output_schema.json."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    core_skills: float = Field(..., ge=0, le=100, description="Core skills score (0-100)")
    technical_concepts: float = Field(..., ge=0, le=100, description="Technical concepts score (0-100)")
    project_experience: float = Field(..., ge=0, le=100, description="Project experience score (0-100)")
    frameworks_tools: float = Field(..., ge=0, le=100, description="Frameworks and tools score (0-100)")
    relevant_experience: float = Field(..., ge=0, le=100, description="Relevant work experience score (0-100)")


class MatchedArea(BaseModel):
    topic: str = Field(..., description="Canonical name of the skill or concept")
    category: str = Field(..., description="Category: core_skills, technical_concepts, frameworks_tools, etc.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    section: str = Field(..., description="Section of resume: Projects, Experience, Skills, Certifications, etc.")
    source: str = Field(..., description="Specific project name, company, or section context")
    evidence: str = Field(..., description="Concrete sentence or phrase extracted from resume proving usage")


class InterviewContextItem(BaseModel):
    topic: str = Field(..., description="Technical topic or skill")
    category: str = Field(..., description="Category from role knowledge base")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Match confidence")
    evidence: str = Field(..., description="Evidence sentence from resume for personalized question generation")
    source: str = Field(..., description="Project name or experience title")


class Feedback(BaseModel):
    strengths: List[str] = Field(default_factory=list, description="Key candidate strengths identified")
    focus_areas: List[str] = Field(default_factory=list, description="Role-relevant areas requiring attention or study")
    resume_improvements: List[str] = Field(default_factory=list, description="Suggestions for improving resume clarity")


class Module1Output(BaseModel):
    selected_role: str = Field(..., description="Selected target role name")
    role_match_score: float = Field(..., ge=0, le=100, description="Deterministic overall role match score (0-100)")
    score_breakdown: ScoreBreakdown = Field(..., description="Breakdown across 5 weighted categories")
    matched_areas: List[MatchedArea] = Field(default_factory=list, description="High-confidence matching skills with evidence")
    partial_matches: List[MatchedArea] = Field(default_factory=list, description="Moderate-confidence or partial matches with evidence")
    missing_areas: List[str] = Field(default_factory=list, description="Key role skills/concepts not demonstrated in resume")
    unrelated_skills: List[str] = Field(default_factory=list, description="Skills present in resume that do not belong to selected role")
    feedback: Feedback = Field(default_factory=Feedback, description="Actionable feedback breakdown")
    interview_context: List[InterviewContextItem] = Field(
        default_factory=list,
        description="Structured context passed to Module 2 for personalized question generation",
    )


class Module1AnalysisRequest(BaseModel):
    role: str = Field(..., description="Selected technical role name or role_id")
    resume_text: Optional[str] = Field(None, description="Pre-extracted or raw resume text")
    candidate_name: Optional[str] = Field(None, description="Candidate name (optional)")
