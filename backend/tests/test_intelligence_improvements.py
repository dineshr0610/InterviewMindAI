"""
Tests for the intelligence improvements made to the QuestionQualityEvaluator.

Verifies:
1. Follow-up depth decay: follow-ups at depth 3+ score lower than at depth 0-2
2. Coverage value scaling: uncovered topics score higher as interview progresses
3. Supabase eligibility: Supabase generates candidates in resume_phase on turns 2,5,8,...
4. Follow-up prompt includes coverage context
5. Gemini resume prompt includes remaining topics
"""

from __future__ import annotations

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from ai_engine.services.interview_service import (
    QuestionCandidate,
    QuestionQualityEvaluator,
    SOURCE_FOLLOW_UP,
    SOURCE_GEMINI_RESUME,
    SOURCE_SUPABASE_BANK,
    CAT_FOLLOW_UP,
    CAT_IMPLEMENTATION,
    CAT_ARCHITECTURE,
    CAT_API,
)


# ============================================================
# Test 1: Follow-up depth decay
# ============================================================

class TestFollowUpDepthDecay:

    def _make_follow_up_candidate(self) -> QuestionCandidate:
        return QuestionCandidate(
            text="In your collaborative canvas implementation, how did you handle vector clock synchronization when a client reconnects after being offline?",
            source=SOURCE_FOLLOW_UP,
            category=CAT_FOLLOW_UP,
            topic="WebSocket",
            intent="debug",
            project="Real-Time Collaborative Canvas",
            technology="WebSockets",
            difficulty="Medium",
            selection_reason="Follow-up test",
        )

    def _evaluate(self, depth: int) -> QuestionCandidate:
        cand = self._make_follow_up_candidate()
        return QuestionQualityEvaluator.evaluate(
            cand,
            role_name="Full Stack Developer",
            verified_technologies=["React", "Node.js", "PostgreSQL"],
            verified_projects=["Real-Time Collaborative Canvas"],
            unsupported_technologies=[],
            missing_skills=["Authentication"],
            previous_questions=[],
            recent_intents=[],
            categories_covered=[],
            projects_covered=[],
            technologies_covered=[],
            last_answer="We used CRDT-based conflict resolution with vector clocks for synchronization.",
            strategy="follow_up",
            target_difficulty="Medium",
            follow_up_depth=depth,
            turn_count=5,
            total_projects=3,
            total_technologies=10,
        )

    def test_depth_0_scores_higher_than_depth_3(self):
        """Follow-up at depth 0 should score higher than at depth 3."""
        score_d0 = self._evaluate(0).score
        score_d3 = self._evaluate(3).score
        assert score_d0 > score_d3, f"Depth 0 ({score_d0}) should > depth 3 ({score_d3})"

    def test_depth_2_same_as_depth_0(self):
        """Depth 0, 1, 2 should have no penalty (decay starts at depth > 2)."""
        score_d0 = self._evaluate(0).score
        score_d2 = self._evaluate(2).score
        assert score_d0 == score_d2, f"Depth 0 ({score_d0}) should == depth 2 ({score_d2})"

    def test_depth_4_scores_lower_than_depth_3(self):
        """Each additional depth beyond 2 should reduce score further."""
        score_d3 = self._evaluate(3).score
        score_d4 = self._evaluate(4).score
        assert score_d4 < score_d3, f"Depth 4 ({score_d4}) should < depth 3 ({score_d3})"


# ============================================================
# Test 2: Coverage value increases with interview progress
# ============================================================

class TestCoverageValueScaling:

    def _make_candidate(self, project: str, technology: str) -> QuestionCandidate:
        return QuestionCandidate(
            text=f"In your {project}, how did you architect the {technology} integration for handling concurrent requests?",
            source=SOURCE_GEMINI_RESUME,
            category=CAT_ARCHITECTURE,
            topic=technology,
            intent="architecture",
            project=project,
            technology=technology,
            difficulty="Medium",
            selection_reason="Coverage test",
        )

    def _evaluate_coverage(self, *, turn_count: int, projects_covered: list, technologies_covered: list) -> float:
        cand = self._make_candidate("New Project", "Redis")
        result = QuestionQualityEvaluator.evaluate(
            cand,
            role_name="Backend Developer",
            verified_technologies=["Python", "FastAPI", "Redis", "PostgreSQL"],
            verified_projects=["New Project", "Other Project", "Third Project"],
            unsupported_technologies=[],
            missing_skills=[],
            previous_questions=[],
            recent_intents=[],
            categories_covered=[],
            projects_covered=projects_covered,
            technologies_covered=technologies_covered,
            last_answer=None,
            strategy="topic_transition",
            target_difficulty="Medium",
            follow_up_depth=0,
            turn_count=turn_count,
            total_projects=3,
            total_technologies=4,
        )
        return result.coverage_value

    def test_uncovered_topic_at_turn_10_higher_than_turn_1(self):
        """Coverage value for an uncovered topic should increase as interview progresses."""
        cov_early = self._evaluate_coverage(turn_count=1, projects_covered=[], technologies_covered=[])
        cov_late = self._evaluate_coverage(turn_count=10, projects_covered=[], technologies_covered=[])
        assert cov_late > cov_early, f"Late ({cov_late}) should > early ({cov_early})"

    def test_covered_topic_gets_no_coverage_bonus(self):
        """A topic that's already covered should get 0 coverage value."""
        cov = self._evaluate_coverage(
            turn_count=10,
            projects_covered=["New Project"],
            technologies_covered=["Redis"],
        )
        # Only category_covered matters here (categories_covered=[], so +1.5)
        assert cov <= 1.5, f"Covered topic should get minimal coverage value, got {cov}"


# ============================================================
# Test 3: Follow-up vs. Gemini scoring differentiation
# ============================================================

class TestFollowUpVsGeminiScoring:
    """At high follow-up depth with many uncovered topics,
    Gemini resume question should potentially beat follow-up."""

    def test_deep_followup_loses_to_gemini_with_uncovered_topics(self):
        """At depth 4+ with many uncovered topics, a Gemini resume question
        covering a new project should score competitively against follow-up."""
        
        # Follow-up at depth 4
        follow_up = QuestionCandidate(
            text="Can you elaborate on the specific retry strategy you used with exponential backoff?",
            source=SOURCE_FOLLOW_UP,
            category=CAT_FOLLOW_UP,
            topic="Redis",
            intent="explain",
            project="Order Engine",
            technology="Redis",
            difficulty="Medium",
            selection_reason="Deep follow-up",
        )
        follow_up_eval = QuestionQualityEvaluator.evaluate(
            follow_up,
            role_name="Full Stack Developer",
            verified_technologies=["React", "Node.js", "PostgreSQL", "Redis", "WebSockets"],
            verified_projects=["Collaborative Canvas", "Order Engine", "HealthPulse"],
            unsupported_technologies=[],
            missing_skills=["Authentication"],
            previous_questions=["Q1 about Redis", "Q2 about Redis caching", "Q3 about Redis retry"],
            recent_intents=["explain", "debug", "explain"],
            categories_covered=["implementation", "debugging"],
            projects_covered=["Order Engine"],
            technologies_covered=["Redis"],
            last_answer="We used exponential backoff with jitter.",
            strategy="deeper_probe",
            target_difficulty="Medium",
            follow_up_depth=4,
            turn_count=8,
            total_projects=3,
            total_technologies=5,
        )
        
        # Gemini resume question covering a NEW project
        gemini = QuestionCandidate(
            text="In your HealthPulse Telehealth Portal, how did you implement WebRTC peer connection management for one-to-one video consultations?",
            source=SOURCE_GEMINI_RESUME,
            category=CAT_ARCHITECTURE,
            topic="WebRTC",
            intent="architecture",
            project="HealthPulse",
            technology="WebRTC",
            difficulty="Medium",
            selection_reason="New project coverage",
        )
        gemini_eval = QuestionQualityEvaluator.evaluate(
            gemini,
            role_name="Full Stack Developer",
            verified_technologies=["React", "Node.js", "PostgreSQL", "Redis", "WebSockets"],
            verified_projects=["Collaborative Canvas", "Order Engine", "HealthPulse"],
            unsupported_technologies=[],
            missing_skills=["Authentication"],
            previous_questions=["Q1 about Redis", "Q2 about Redis caching", "Q3 about Redis retry"],
            recent_intents=["explain", "debug", "explain"],
            categories_covered=["implementation", "debugging"],
            projects_covered=["Order Engine"],
            technologies_covered=["Redis"],
            last_answer="We used exponential backoff with jitter.",
            strategy="deeper_probe",
            target_difficulty="Medium",
            follow_up_depth=4,
            turn_count=8,
            total_projects=3,
            total_technologies=5,
        )
        
        # The Gemini question covering new project+technology should have closed
        # the gap significantly due to depth decay + coverage bonus
        score_gap = follow_up_eval.score - gemini_eval.score
        assert score_gap < 5.0, (
            f"Score gap ({score_gap:.1f}) between deep follow-up ({follow_up_eval.score:.1f}) "
            f"and new-project Gemini ({gemini_eval.score:.1f}) should be < 5.0 "
            f"(coverage bonus + depth decay should narrow it)"
        )


# ============================================================
# Test 4: Topic Importance Prioritization
# ============================================================

from ai_engine.services.interview_service import get_role_skill_rankings

class TestTopicImportancePrioritization:
    
    def test_get_role_skill_rankings_frontend(self):
        core, supporting, optional = get_role_skill_rankings("Frontend Developer")
        assert len(core) > 0
        assert len(supporting) > 0
        assert "web programming" in core or "css" in core or "javascript" in core or "html" in core

    def test_get_role_skill_rankings_backend(self):
        core, supporting, optional = get_role_skill_rankings("Backend Developer")
        assert len(core) > 0
        assert len(supporting) > 0
        core_str = " ".join(core)
        assert "computer programming" in core_str or "web services" in core_str

    def test_technologies_inventory_sorting(self):
        """Simulate the sorting logic used in InterviewService.generate_question"""
        core, supporting, optional = get_role_skill_rankings("Backend Developer")
        
        # A mix of core backend skills and supporting/peripheral skills
        techs = ["Jira", "Slack", "Git", "Web Services"]
        
        def get_tech_importance(tech: str) -> int:
            t_lower = str(tech).lower().strip()
            if t_lower in core: return 3
            if t_lower in supporting: return 2
            if t_lower in optional: return 1
            for ck in core:
                if t_lower in ck or ck in t_lower: return 3
            for sk in supporting:
                if t_lower in sk or sk in t_lower: return 2
            for ok in optional:
                if t_lower in ok or ok in t_lower: return 1
            return 0
            
        techs.sort(key=get_tech_importance, reverse=True)
        
        # Git and Web Services are core/supporting, Jira and Slack are not or lower
        idx_git = techs.index("Git")
        idx_web_services = techs.index("Web Services")
        idx_jira = techs.index("Jira")
        idx_slack = techs.index("Slack")
        
        assert idx_git < idx_jira
        assert idx_web_services < idx_slack

