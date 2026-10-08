"""
PHASE 4B Integration Tests — AI Analysis Output in Adaptive Flow

Verifies that:
1. initial_assessment_state correctly carries ai_focus_areas and ai_skill_gaps
2. choose_next_topic prefers AI focus areas over generic role topics
3. adapt_after_answer forwards ai_focus_areas and ai_skill_gaps
4. build_final_assessment enriches the final report with AI analysis fields
5. detect_skill_gaps merges ai_skill_gaps without removing deterministic gaps
6. AI fields default gracefully when ai_analysis is absent
"""

from __future__ import annotations
from typing import Any, Dict
import pytest
from app.domain.adaptive import initial_assessment_state, choose_next_topic, adapt_after_answer
from app.domain.assessment import build_final_assessment, detect_skill_gaps


def _role(important_topics=None):
    return {"id": "backend", "name": "Backend Developer", "selected_name": "Backend Developer",
            "important_topics": important_topics if important_topics is not None else ["REST API", "Databases", "Concurrency"],
            "required_skills": ["Python", "SQL"]}

def _resume_match(ai_focus_areas=None, ai_skill_gaps=None, analysis_source="gemini", question_mode="resume_grounded"):
    return {"question_mode": question_mode, "matched_skills": ["Python", "FastAPI"],
            "missing_skills": ["Kubernetes"], "resume_topics": ["Python", "FastAPI"],
            "topic_inventory": {"projects": [{"name": "E-Commerce App"}], "technologies": ["PostgreSQL"]},
            "ai_focus_areas": ai_focus_areas or [], "ai_skill_gaps": ai_skill_gaps or [],
            "analysis_source": analysis_source}


class TestInitialAssessmentState:
    def test_ai_focus_areas_stored_in_state(self):
        focus = ["System Design", "Async Programming"]
        rm = _resume_match(ai_focus_areas=focus, ai_skill_gaps=["Docker"])
        state = initial_assessment_state(_role(), rm, None, "Easy")
        assert state["ai_focus_areas"] == focus
        assert state["ai_skill_gaps"] == ["Docker"]
        assert state["analysis_source"] == "gemini"

    def test_empty_ai_fields_default_gracefully(self):
        rm = {"question_mode": "foundational", "matched_skills": []}
        state = initial_assessment_state(_role(), rm, None, "Easy")
        assert state["ai_focus_areas"] == []
        assert state["ai_skill_gaps"] == []
        assert state["analysis_source"] == "deterministic"

    def test_analysis_source_deterministic_when_not_set(self):
        rm = _resume_match(analysis_source=None)
        state = initial_assessment_state(_role(), rm, None, "Easy")
        assert state["analysis_source"] == "deterministic"


class TestChooseNextTopicWithAIAreas:
    def _call(self, topics_covered=None, ai_focus_areas=None, ai_skill_gaps=None):
        return choose_next_topic(role=_role(important_topics=["REST API", "Databases"]),
            current_topic="Python", topic_scores={"Python": 7}, technical_score=7,
            strategy="topic_transition", missing_points=[],
            topic_inventory={"projects": [], "technologies": []},
            matched_resume_topics=[], missing_skills=["Kubernetes"],
            topics_covered=topics_covered or ["Python"],
            ai_focus_areas=ai_focus_areas or [], ai_skill_gaps=ai_skill_gaps or [])

    def test_ai_focus_area_beats_generic_role_topic(self):
        assert self._call(ai_focus_areas=["System Design"]) == "System Design"

    def test_ai_skill_gap_beats_role_important_topic(self):
        # AI skill gaps score 5.5, role topics 4.0
        topic = self._call(ai_skill_gaps=["Docker"])
        # Docker (5.5) > REST API (4.0) > Databases (4.0)
        assert topic == "Docker"

    def test_covered_ai_focus_area_skipped(self):
        topic = self._call(ai_focus_areas=["System Design"], topics_covered=["Python", "System Design"])
        assert topic != "System Design"

    def test_no_ai_areas_falls_back_to_missing_skills(self):
        assert self._call() == "Kubernetes"

    def test_no_candidates_returns_current_topic(self):
        result = choose_next_topic(role=_role(important_topics=[]), current_topic="Python",
            topic_scores={}, technical_score=5, strategy="topic_transition", missing_points=[],
            topic_inventory={"projects": [], "technologies": []}, matched_resume_topics=[],
            missing_skills=[], topics_covered=["Python"], ai_focus_areas=[], ai_skill_gaps=[])
        assert result == "Python"


class TestAdaptAfterAnswerPreservesAIAreas:
    def _state_with_ai(self):
        rm = _resume_match(ai_focus_areas=["Microservices", "CI/CD"], ai_skill_gaps=["Docker"])
        return initial_assessment_state(_role(), rm, None, "Easy")

    def test_ai_focus_areas_preserved_after_adaptation(self):
        state = self._state_with_ai()
        new_state = adapt_after_answer(state=state, role=_role(), technical_score=7,
            current_topic=state["current_topic"], current_difficulty="Easy", concept="Python",
            missing_points=[], strengths=["Good"], weaknesses=[])
        assert "Microservices" in new_state["ai_focus_areas"]
        assert "CI/CD" in new_state["ai_focus_areas"]
        assert "Docker" in new_state["ai_skill_gaps"]


class TestBuildFinalAssessmentAIEnrichment:
    def _messages(self):
        return [{"answer": "FastAPI with PostgreSQL", "score": 7, "technical_score": 7,
                 "communication_score": 8, "technical_strengths": ["Good API design"],
                 "technical_weaknesses": ["Missed caching"], "communication_strengths": [],
                 "communication_improvements": [], "topic": "FastAPI"}]

    def _rm_with_m1(self, ai_analysis=None):
        rm = _resume_match()
        rm["module1_output"] = {"analysis_source": "gemini",
            "ai_analysis": ai_analysis or {"interview_focus_areas": ["Async programming", "DB indexing"],
                "skill_gaps": ["Docker", "K8s"], "transferable_skills": ["Problem solving"]}}
        return rm

    def test_analysis_source_in_final_assessment(self):
        a = build_final_assessment(candidate_name="Alice", role=_role(), profile={"skills": ["Python"]},
            resume_match=self._rm_with_m1(), messages=self._messages())
        assert a["analysis_source"] == "gemini"

    def test_ai_focus_areas_in_final_assessment(self):
        a = build_final_assessment(candidate_name="Alice", role=_role(), profile={"skills": ["Python"]},
            resume_match=self._rm_with_m1(), messages=self._messages())
        assert "Async programming" in a["ai_interview_focus_areas"]

    def test_ai_transferable_skills_in_final_assessment(self):
        a = build_final_assessment(candidate_name="Alice", role=_role(), profile={"skills": ["Python"]},
            resume_match=self._rm_with_m1(), messages=self._messages())
        assert "Problem solving" in a["ai_transferable_skills"]

    def test_no_ai_analysis_defaults_gracefully(self):
        a = build_final_assessment(candidate_name="Bob", role=_role(), profile={"skills": ["Python"]},
            resume_match=_resume_match(analysis_source="deterministic"), messages=self._messages())
        assert a["analysis_source"] == "deterministic"
        assert a["ai_interview_focus_areas"] == []
        assert a["ai_transferable_skills"] == []


class TestDetectSkillGapsWithAI:
    def test_ai_identified_gaps_in_output(self):
        gaps = detect_skill_gaps(role=_role(), resume_match={"missing_skills": ["SQL"]},
            weak_topics=[], technical_weaknesses=[], coding=None, communication_weaknesses=[],
            ai_skill_gaps=["Docker", "Kubernetes"], ai_focus_areas=["System Design"])
        assert "Docker" in gaps["ai_identified_gaps"]
        assert "SQL" in gaps["missing_skills"]

    def test_ai_focus_areas_not_covered_tracked(self):
        gaps = detect_skill_gaps(role=_role(), resume_match={"missing_skills": []},
            weak_topics=[{"topic": "System Design", "score": 3}], technical_weaknesses=[],
            coding=None, communication_weaknesses=[],
            ai_skill_gaps=[], ai_focus_areas=["Async IO", "System Design"])
        assert "Async IO" in gaps["ai_focus_areas_not_covered"]
        assert "System Design" not in gaps["ai_focus_areas_not_covered"]

    def test_no_ai_input_backward_compatible(self):
        gaps = detect_skill_gaps(role=_role(), resume_match={"missing_skills": ["Docker"]},
            weak_topics=[], technical_weaknesses=[], coding=None, communication_weaknesses=[])
        assert "Docker" in gaps["missing_skills"]
        assert gaps["ai_identified_gaps"] == []
        assert gaps["ai_focus_areas_not_covered"] == []
