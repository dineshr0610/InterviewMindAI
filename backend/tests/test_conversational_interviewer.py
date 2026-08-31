"""Tests for the conversational interviewer / context-aware follow-ups.

Covers the LangGraph behavioral improvements:
  - next-question strategy selection from the candidate's score
  - high score -> deeper probing / tradeoffs / edge cases
  - medium score -> clarification / follow-up
  - low score -> simpler fundamentals / recovery
  - follow-up depth is capped and topics eventually transition
  - the last answer + strategy are passed into question generation
  - resume context remains available (no regression)
  - duplicate prevention, RAG, adaptive difficulty and LangGraph remain active
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from ai_engine.graphs.interview_graph import interview_graph
from ai_engine.services.question_controller import (
    ARCHITECTURE,
    CLARIFICATION,
    DEEPER_PROBE,
    EDGE_CASE,
    FOLLOW_UP,
    FUNDAMENTALS,
    MAX_FOLLOW_UP_DEPTH,
    SCENARIO,
    TOPIC_TRANSITION,
    TRADEOFF,
    choose_next_strategy,
)


def _run_answer_turn(graph_kwargs: dict):
    """Invoke the compiled graph for a single answer turn."""
    with patch("ai_engine.graphs.interview_nodes.service.generate_question") as generate, \
         patch("ai_engine.graphs.interview_nodes.evaluation_service.evaluate") as evaluate:
        generate.return_value = {"answer": "What would you change in production?"}
        evaluate.return_value = {
            "score": graph_kwargs.get("score", 8),
            "feedback": "Feedback.",
            "strengths": ["Strength"],
            "improvements": ["Improvement"],
            "next_strategy": "",
            "summary": "",
        }
        return interview_graph.invoke(graph_kwargs), generate, evaluate


def _make_kwargs(score: int = 8, depth: int = 0, topic: str = "Backend Development", **over):
    base = {
        "mode": "answer", "candidate_name": "Dinesh", "topic": topic,
        "difficulty": "Medium", "question": "How does Redis caching work?",
        "answer": "I would use Redis to cache frequently accessed API responses.",
        "score": 0, "feedback": "", "strengths": [], "improvements": [],
        "question_number": 1, "max_questions": 50, "interview_completed": False,
        "history": [], "resume_text": "Built a FastAPI backend using PostgreSQL and Redis.",
        "next_strategy": "", "follow_up_depth": depth,
    }
    base.update(over)
    base["score"] = score
    return base


# ===========================================================================
# Strategy selection (unit tests of choose_next_strategy)
# ===========================================================================

class TestChooseNextStrategy:

    def test_high_score_probes_deeper(self) -> None:
        assert choose_next_strategy(9, 0) in {DEEPER_PROBE, EDGE_CASE, TRADEOFF, SCENARIO, ARCHITECTURE}

    def test_medium_score_clarifies_or_follows_up(self) -> None:
        assert choose_next_strategy(6, 0) in {FOLLOW_UP, CLARIFICATION, DEEPER_PROBE}

    def test_low_score_tests_fundamentals(self) -> None:
        assert choose_next_strategy(2, 0) in {FUNDAMENTALS, CLARIFICATION, FOLLOW_UP}

    def test_deep_depth_forces_transition(self) -> None:
        assert choose_next_strategy(8, MAX_FOLLOW_UP_DEPTH) == TOPIC_TRANSITION
        assert choose_next_strategy(3, MAX_FOLLOW_UP_DEPTH) == TOPIC_TRANSITION

    def test_low_score_on_transition_still_transitions(self) -> None:
        # Even a struggling candidate should not be forced deeper once the
        # subject has been covered enough.
        assert choose_next_strategy(1, MAX_FOLLOW_UP_DEPTH) == TOPIC_TRANSITION


# ===========================================================================
# Graph-level: strategy is computed and question generator receives it
# ===========================================================================

class TestGraphConversationalFlow:

    def test_generate_question_receives_strategy_and_last_answer(self) -> None:
        result, generate, _ = _run_answer_turn(_make_kwargs(score=9, depth=0))
        assert result["next_strategy"] in {DEEPER_PROBE, EDGE_CASE, TRADEOFF, SCENARIO, ARCHITECTURE}
        call_kwargs = generate.call_args.kwargs
        assert call_kwargs["strategy"] == result["next_strategy"]
        assert call_kwargs["last_answer"] == _make_kwargs(9, 0)["answer"]

    def test_high_score_leads_to_deep_strategy(self) -> None:
        result, generate, _ = _run_answer_turn(_make_kwargs(score=9, depth=0))
        assert result["next_strategy"] in {DEEPER_PROBE, EDGE_CASE, TRADEOFF, SCENARIO, ARCHITECTURE}

    def test_low_score_leads_to_recovery_strategy(self) -> None:
        result, _, _ = _run_answer_turn(_make_kwargs(score=2, depth=0))
        assert result["next_strategy"] in {FUNDAMENTALS, CLARIFICATION, FOLLOW_UP}

    def test_medium_score_leads_to_clarification_or_follow_up(self) -> None:
        result, _, _ = _run_answer_turn(_make_kwargs(score=6, depth=0))
        assert result["next_strategy"] in {FOLLOW_UP, CLARIFICATION, DEEPER_PROBE}

    def test_follow_up_depth_increments_on_deepening(self) -> None:
        result, _, _ = _run_answer_turn(_make_kwargs(score=9, depth=0))
        assert result["follow_up_depth"] == 1

    def test_follow_up_depth_resets_on_transition(self) -> None:
        result, _, _ = _run_answer_turn(_make_kwargs(score=9, depth=MAX_FOLLOW_UP_DEPTH))
        assert result["follow_up_depth"] == 0
        assert result["next_strategy"] == TOPIC_TRANSITION

    def test_difficulty_still_adapts(self) -> None:
        result, _, _ = _run_answer_turn(_make_kwargs(score=9, depth=0, difficulty="Medium"))
        assert result["difficulty"] == "Hard"


# ===========================================================================
# Regression: existing behaviors remain active
# ===========================================================================

class TestConversationalRegressions:

    def test_duplicate_prevention_still_active(self) -> None:
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Backend Development")
        valid, reason = ctrl.validate(
            "What is Backend Development and why is it useful?",
            ["What is Backend Development and why is it useful?"],
        )
        assert not valid
        assert reason == "duplicate"

    def test_resume_context_passed_to_question_generation(self) -> None:
        result, generate, _ = _run_answer_turn(_make_kwargs(score=9, depth=0))
        call_kwargs = generate.call_args.kwargs
        assert call_kwargs["resume_text"] == "Built a FastAPI backend using PostgreSQL and Redis."

    def test_start_turn_still_generates_first_question(self) -> None:
        with patch("ai_engine.graphs.interview_nodes.service.generate_question") as generate:
            generate.return_value = {"answer": "Tell me about your FastAPI backend."}
            start = interview_graph.invoke({
                "mode": "start", "candidate_name": "Dinesh", "topic": "Backend Development",
                "difficulty": "Medium", "question": "", "answer": "", "score": 0,
                "feedback": "", "strengths": [], "improvements": [], "question_number": 0,
                "max_questions": 50, "interview_completed": False, "history": [],
                "resume_text": "Built a FastAPI backend.", "next_strategy": "", "follow_up_depth": 0,
            })
        assert start["question"] == "Tell me about your FastAPI backend."

    def test_can_continue_beyond_three_and_five_questions(self) -> None:
        # Safety limit is high; a turn with a next question stays active even
        # past question index 3.
        result, _, _ = _run_answer_turn(_make_kwargs(score=8, depth=0, question_number=6, max_questions=50))
        assert result["interview_completed"] is False
        assert result["question"] == "What would you change in production?"
