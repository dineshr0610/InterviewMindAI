import pytest
from unittest.mock import patch
from app.resume_processing.service import get_resume_processing_service
from app.resume_processing.ai_analyzer import AIResumeAnalyzer
from app.resume_processing.schemas import Module1Output

DUMMY_RESUME_TEXT = """
Dinesh - Full Stack Developer
Skills: Python, FastAPI, JavaScript, React, PostgreSQL
Projects:
- Personal Portfolio: Built with React and FastAPI.
- Data Service: Developed asynchronous data processing pipeline using Python and PostgreSQL.
"""

MOCK_AI_DATA = {
    "summary": "Candidate possesses practical experience in full-stack Python and FastAPI development.",
    "core_requirements": [
        {
            "requirement": "Python",
            "importance": "high",
            "status": "strong_match",
            "evidence": ["Python, FastAPI"],
            "confidence": 0.95
        }
    ],
    "supporting_requirements": [
        {
            "requirement": "PostgreSQL",
            "importance": "medium",
            "status": "strong_match",
            "evidence": ["PostgreSQL"],
            "confidence": 0.9
        }
    ],
    "technology_matches": [
        {
            "technology": "Python",
            "status": "strong_match",
            "evidence": ["Python"],
            "confidence": 0.95
        }
    ],
    "strong_matches": ["Python"],
    "partial_matches": [],
    "missing_or_unverified": ["Java", "C++"],
    "relevant_projects": [
        {
            "project": "Data Service",
            "relevance": "Demonstrates asynchronous pipeline design in Python.",
            "evidence": ["Developed asynchronous data processing pipeline using Python and PostgreSQL."]
        }
    ],
    "skill_gaps": ["Java", "Docker"],
    "transferable_skills": ["API Design"],
    "interview_focus_areas": [
        "Inquire about PostgreSQL query optimization techniques."
    ]
}


def test_test1_gemini_succeeds_ai_analysis_populated():
    service = get_resume_processing_service()
    with patch.object(AIResumeAnalyzer, "analyze", return_value=MOCK_AI_DATA):
        output: Module1Output = service.process(
            resume_data=DUMMY_RESUME_TEXT.encode("utf-8"),
            role="full_stack_developer",
            candidate_name="Dinesh"
        )
        assert output.ai_analysis is not None
        assert output.analysis_source in ("gemini", "hybrid")
        assert output.ai_analysis["summary"] == MOCK_AI_DATA["summary"]
        assert len(output.ai_analysis["core_requirements"]) == 1
        assert len(output.ai_analysis["relevant_projects"]) == 1


def test_test2_gemini_fails_ai_analysis_null():
    service = get_resume_processing_service()
    with patch.object(AIResumeAnalyzer, "analyze", return_value=None):
        output: Module1Output = service.process(
            resume_data=DUMMY_RESUME_TEXT.encode("utf-8"),
            role="full_stack_developer",
            candidate_name="Dinesh"
        )
        assert output.ai_analysis is None
        assert output.analysis_source == "deterministic"


def test_test3_gemini_fails_no_fabricated_fit_claim():
    service = get_resume_processing_service()
    with patch.object(AIResumeAnalyzer, "analyze", return_value=None):
        output: Module1Output = service.process(
            resume_data=DUMMY_RESUME_TEXT.encode("utf-8"),
            role="full_stack_developer",
            candidate_name="Dinesh"
        )
        output_dict = output.model_dump()
        # Ensure no fabricated fit label is emitted in the output contract
        assert "fit_level" not in output_dict
        assert output.ai_analysis is None


def test_test4_test5_gemini_fails_no_ai_recommendations_or_interviewer_focus():
    service = get_resume_processing_service()
    with patch.object(AIResumeAnalyzer, "analyze", return_value=None):
        output: Module1Output = service.process(
            resume_data=DUMMY_RESUME_TEXT.encode("utf-8"),
            role="full_stack_developer",
            candidate_name="Dinesh"
        )
        assert output.ai_analysis is None
        # Feedback focus_areas must not claim to be AI-derived
        assert output.analysis_source == "deterministic"


def test_test6_gemini_fails_explicit_resume_facts_preserved():
    service = get_resume_processing_service()
    with patch.object(AIResumeAnalyzer, "analyze", return_value=None):
        output: Module1Output = service.process(
            resume_data=DUMMY_RESUME_TEXT.encode("utf-8"),
            role="full_stack_developer",
            candidate_name="Dinesh"
        )
        # Explicit resume facts are preserved in matched_areas
        topics = [m.topic.lower() for m in output.matched_areas]
        assert "python" in topics
        # Evidence is preserved from the resume text
        python_match = next(m for m in output.matched_areas if m.topic.lower() == "python")
        assert python_match.evidence is not None


def test_test7_gemini_succeeds_evidence_comes_from_ai_analysis():
    service = get_resume_processing_service()
    with patch.object(AIResumeAnalyzer, "analyze", return_value=MOCK_AI_DATA):
        output: Module1Output = service.process(
            resume_data=DUMMY_RESUME_TEXT.encode("utf-8"),
            role="full_stack_developer",
            candidate_name="Dinesh"
        )
        assert output.ai_analysis is not None
        req = output.ai_analysis["core_requirements"][0]
        assert req["evidence"] == ["Python, FastAPI"]
        proj = output.ai_analysis["relevant_projects"][0]
        assert "PostgreSQL" in proj["evidence"][0]


def test_test8_gemini_succeeds_frontend_contract_fidelity():
    service = get_resume_processing_service()
    with patch.object(AIResumeAnalyzer, "analyze", return_value=MOCK_AI_DATA):
        output: Module1Output = service.process(
            resume_data=DUMMY_RESUME_TEXT.encode("utf-8"),
            role="full_stack_developer",
            candidate_name="Dinesh"
        )
        data = output.model_dump()
        # Verify complete schema fields expected by Module1AnalysisResult
        assert "selected_role" in data
        assert "role_match_score" in data
        assert "score_breakdown" in data
        assert "matched_areas" in data
        assert "missing_areas" in data
        assert "ai_analysis" in data
        assert "analysis_source" in data
        assert data["analysis_source"] == "hybrid"
