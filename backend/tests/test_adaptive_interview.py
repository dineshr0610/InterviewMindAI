"""Comprehensive Week 1 adaptive interview tests.

Covers:
  A. Strong answer  — difficulty increases
  B. Weak answer    — difficulty decreases
  C. Medium answer  — difficulty unchanged
  D. Multi-turn adaptation
  E. Topic continuity
  F. Duplicate question prevention
  G. max_questions completion
  H. Post-completion answer rejection
  I. Question continuity regression (Q1->Q2->Q3)
  J. Question progression (concept deepening)
"""

from __future__ import annotations

import re
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.interview import InterviewStatus
from app.services.interview_service import InterviewService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_interview(
    interview_id=None,
    topic: str = "Binary Search",
    difficulty: str = "Medium",
    max_questions: int = 5,
    status: InterviewStatus = InterviewStatus.ACTIVE,
    resume_text: str | None = None,
):
    return SimpleNamespace(
        id=interview_id or uuid4(),
        topic=topic,
        difficulty=difficulty,
        max_questions=max_questions,
        status=status,
        resume_text=resume_text,
    )


def _pending_message(question: str = "What is Binary Search?"):
    return SimpleNamespace(id=uuid4(), question=question, answer=None)


def _eval(score: int = 8, next_question: str | None = "Next Q?", difficulty: str | None = "Medium"):
    return {
        "score": score,
        "feedback": f"Feedback for score {score}.",
        "strengths": ["Strength A"],
        "improvements": ["Improvement B"],
        "next_question": next_question,
        "difficulty": difficulty,
        "completed": False,
    }


def _mock_repo(interview, latest_msg=None):
    """Build a repository mock with all async methods properly set up."""
    repo = MagicMock()
    repo.get_interview = AsyncMock(return_value=interview)
    repo.get_latest_message = AsyncMock(return_value=latest_msg or _pending_message())
    repo.update_message = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
    repo.save_message = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
    repo.get_messages = AsyncMock(return_value=[])
    repo.get_answered_message_count = AsyncMock(return_value=0)
    repo.update_interview_difficulty = AsyncMock()
    repo.finish_interview = AsyncMock()
    return repo


# ===========================================================================
# A. Strong answer — difficulty increases
# ===========================================================================

class TestStrongAnswerDifficultyIncrease:

    @pytest.mark.asyncio
    async def test_easy_to_medium_on_high_score(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, difficulty="Easy")

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(return_value=_eval(score=9, difficulty="Medium"))
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(interview)

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["difficulty"] == "Medium"
        svc.repository.update_interview_difficulty.assert_awaited_once_with(iid, "Medium")

    @pytest.mark.asyncio
    async def test_medium_to_hard_on_high_score(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, difficulty="Medium")

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(return_value=_eval(score=10, difficulty="Hard"))
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(interview)

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["difficulty"] == "Hard"
        svc.repository.update_interview_difficulty.assert_awaited_once_with(iid, "Hard")

    @pytest.mark.asyncio
    async def test_hard_stays_hard_on_high_score(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, difficulty="Hard")

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(return_value=_eval(score=9, difficulty="Hard"))
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(interview)

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["difficulty"] == "Hard"


# ===========================================================================
# B. Weak answer — difficulty decreases
# ===========================================================================

class TestWeakAnswerDifficultyDecrease:

    @pytest.mark.asyncio
    async def test_hard_to_medium_on_low_score(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, difficulty="Hard")

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(return_value=_eval(score=3, difficulty="Medium"))
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(interview)

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["difficulty"] == "Medium"
        svc.repository.update_interview_difficulty.assert_awaited_once_with(iid, "Medium")

    @pytest.mark.asyncio
    async def test_medium_to_easy_on_low_score(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, difficulty="Medium")

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(return_value=_eval(score=2, difficulty="Easy"))
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(interview)

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["difficulty"] == "Easy"
        svc.repository.update_interview_difficulty.assert_awaited_once_with(iid, "Easy")

    @pytest.mark.asyncio
    async def test_easy_stays_easy_on_low_score(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, difficulty="Easy")

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(return_value=_eval(score=1, difficulty="Easy"))
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(interview)

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["difficulty"] == "Easy"


# ===========================================================================
# C. Medium answer — difficulty unchanged
# ===========================================================================

class TestMediumAnswerDifficultyUnchanged:

    @pytest.mark.asyncio
    async def test_score_6_keeps_medium(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, difficulty="Medium")

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(return_value=_eval(score=6, difficulty="Medium"))
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(interview)

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["difficulty"] == "Medium"
        svc.repository.update_interview_difficulty.assert_not_called()

    @pytest.mark.asyncio
    async def test_score_7_keeps_hard(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, difficulty="Hard")

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(return_value=_eval(score=7, difficulty="Hard"))
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(interview)

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["difficulty"] == "Hard"
        svc.repository.update_interview_difficulty.assert_not_called()

    @pytest.mark.asyncio
    async def test_score_5_keeps_easy(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, difficulty="Easy")

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(return_value=_eval(score=5, difficulty="Easy"))
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(interview)

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["difficulty"] == "Easy"
        svc.repository.update_interview_difficulty.assert_not_called()


# ===========================================================================
# D. Multi-turn adaptation
# ===========================================================================

class TestMultiTurnAdaptation:

    @pytest.mark.asyncio
    async def test_difficulty_escalates_across_turns(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, difficulty="Easy", max_questions=3)

        turn_returns = [
            {**_eval(9, "Q2?", "Medium"), "completed": False},
            {**_eval(9, "Q3?", "Hard"), "completed": False},
            {**_eval(9, None, "Hard"), "completed": True},
        ]

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(side_effect=turn_returns)
            svc = InterviewService(MagicMock())

        repo = _mock_repo(interview)
        repo.get_answered_message_count = AsyncMock(side_effect=[0, 1, 2])
        svc.repository = repo

        r1 = await svc.submit_answer(iid, "A" * 50)
        assert r1["difficulty"] == "Medium"

        r2 = await svc.submit_answer(iid, "B" * 50)
        assert r2["difficulty"] == "Hard"

        r3 = await svc.submit_answer(iid, "C" * 50)
        assert r3["difficulty"] == "Hard"
        assert r3["status"] == "completed"

    @pytest.mark.asyncio
    async def test_difficulty_decreases_across_turns(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, difficulty="Hard", max_questions=3)

        turn_returns = [
            {**_eval(2, "Q2?", "Medium"), "completed": False},
            {**_eval(3, "Q3?", "Easy"), "completed": False},
            {**_eval(1, None, "Easy"), "completed": True},
        ]

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(side_effect=turn_returns)
            svc = InterviewService(MagicMock())

        repo = _mock_repo(interview)
        repo.get_answered_message_count = AsyncMock(side_effect=[0, 1, 2])
        svc.repository = repo

        r1 = await svc.submit_answer(iid, "A" * 50)
        assert r1["difficulty"] == "Medium"

        r2 = await svc.submit_answer(iid, "B" * 50)
        assert r2["difficulty"] == "Easy"

        r3 = await svc.submit_answer(iid, "C" * 50)
        assert r3["difficulty"] == "Easy"
        assert r3["status"] == "completed"


# ===========================================================================
# E. Topic continuity
# ===========================================================================

class TestTopicContinuity:

    @pytest.mark.asyncio
    async def test_topic_passed_to_provider(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, topic="SQL Joins", difficulty="Easy")

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(return_value=_eval(7, "Q2?", "Easy"))
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(interview, _pending_message("Explain INNER JOIN."))

        await svc.submit_answer(iid, "INNER JOIN returns matching rows from both tables.")

        call_kwargs = pc.return_value.process_answer.call_args.kwargs
        assert call_kwargs["topic"] == "SQL Joins"

    @pytest.mark.asyncio
    async def test_topic_preserved_after_difficulty_change(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, topic="Java OOP", difficulty="Medium")

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(return_value=_eval(9, "Q2?", "Hard"))
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(interview)

        await svc.submit_answer(iid, "Encapsulation hides internal state.")

        call_kwargs = pc.return_value.process_answer.call_args.kwargs
        assert call_kwargs["topic"] == "Java OOP"
        assert call_kwargs["difficulty"] == "Medium"


# ===========================================================================
# F. Duplicate question prevention
# ===========================================================================

class TestDuplicateQuestionPrevention:

    def test_exact_duplicate_rejected(self) -> None:
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Binary Search")
        valid, reason = ctrl.validate(
            "What is Binary Search?",
            ["What is Binary Search?"],
        )
        assert not valid
        assert reason == "duplicate"

    def test_near_duplicate_rejected(self) -> None:
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Binary Search")
        valid, reason = ctrl.validate(
            "What is Binary Search and why is it useful for sorting and searching?",
            ["What is Binary Search and why is it useful for searching data?"],
        )
        assert not valid
        assert reason == "near_duplicate"

    def test_different_question_accepted(self) -> None:
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Binary Search")
        valid, reason = ctrl.validate(
            "What are the time and space complexities of Binary Search?",
            ["What is Binary Search, and why is it useful?"],
        )
        assert valid
        assert reason == "valid"

    def test_topic_missing_rejected(self) -> None:
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Binary Search")
        valid, reason = ctrl.validate(
            "Explain the quicksort algorithm in detail.",
            [],
        )
        assert not valid
        assert reason == "topic_missing"

    def test_empty_question_rejected(self) -> None:
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Binary Search")
        valid, reason = ctrl.validate("", [])
        assert not valid
        assert reason == "empty"

    def test_short_question_rejected(self) -> None:
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Binary Search")
        valid, reason = ctrl.validate("Short?", [])
        assert not valid
        assert reason == "empty"


# ===========================================================================
# G. max_questions completion
# ===========================================================================

class TestMaxQuestionsCompletion:

    @pytest.mark.asyncio
    async def test_max_1_completes_after_one_answer(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, max_questions=1)

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(
                return_value=_eval(7, "Next irrelevant", None)
            )
            svc = InterviewService(MagicMock())

        repo = _mock_repo(interview)
        repo.get_answered_message_count = AsyncMock(return_value=1)
        svc.repository = repo

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["status"] == "completed"
        assert result["next_question"] is None
        repo.finish_interview.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_max_3_completes_after_three_answers(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, max_questions=3)

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(
                return_value=_eval(7, "Next", None)
            )
            svc = InterviewService(MagicMock())

        repo = _mock_repo(interview)
        repo.get_answered_message_count = AsyncMock(return_value=3)
        svc.repository = repo

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["status"] == "completed"
        repo.finish_interview.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_next_question_completes_interview(self) -> None:
        iid = uuid4()
        interview = _make_interview(iid, max_questions=5)

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(
                return_value=_eval(7, None, None)
            )
            svc = InterviewService(MagicMock())

        repo = _mock_repo(interview)
        repo.get_answered_message_count = AsyncMock(return_value=2)
        svc.repository = repo

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["status"] == "completed"
        repo.finish_interview.assert_awaited_once()


# ===========================================================================
# H. Post-completion answer rejection
# ===========================================================================

class TestPostCompletionRejection:

    @pytest.mark.asyncio
    async def test_answer_rejected_after_completed(self) -> None:
        from app.core.exceptions import InterviewAlreadyEndedException

        iid = uuid4()
        interview = _make_interview(iid, status=InterviewStatus.COMPLETED)

        with patch("app.services.interview_service.AIProvider"):
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(interview)

        with pytest.raises(InterviewAlreadyEndedException):
            await svc.submit_answer(iid, "This should be rejected.")

    @pytest.mark.asyncio
    async def test_answer_rejected_for_inactive_interview(self) -> None:
        from app.core.exceptions import InterviewNotActiveException

        iid = uuid4()
        interview = _make_interview(iid, status=InterviewStatus.TERMINATED)

        with patch("app.services.interview_service.AIProvider"):
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(interview)

        with pytest.raises(InterviewNotActiveException):
            await svc.submit_answer(iid, "This should be rejected too.")

    @pytest.mark.asyncio
    async def test_answer_rejected_for_nonexistent_interview(self) -> None:
        from app.core.exceptions import InterviewNotFoundException

        iid = uuid4()

        with patch("app.services.interview_service.AIProvider"):
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(None)
        svc.repository.get_interview = AsyncMock(return_value=None)

        with pytest.raises(InterviewNotFoundException):
            await svc.submit_answer(iid, "No interview exists.")

    @pytest.mark.asyncio
    async def test_answer_too_short_rejected(self) -> None:
        from app.core.exceptions import InvalidAnswerException

        iid = uuid4()
        interview = _make_interview(iid)

        with patch("app.services.interview_service.AIProvider"):
            svc = InterviewService(MagicMock())

        svc.repository = _mock_repo(interview)

        with pytest.raises(InvalidAnswerException):
            await svc.submit_answer(iid, "Short")


# ===========================================================================
# I. Question continuity regression (Q1->answer->Q2->answer->Q3)
# ===========================================================================

class TestQuestionContinuityRegression:

    @pytest.mark.asyncio
    async def test_two_turn_continuity(self) -> None:
        """Full Q1->answer->Q2->answer->Q3 flow with correct DB operations."""
        iid = uuid4()
        interview = _make_interview(iid, max_questions=3)

        q1_msg = _pending_message("What is Binary Search, and why is it useful?")

        with patch("app.services.interview_service.AIProvider") as pc:
            turn_returns = [
                _eval(8, "How does Binary Search reduce the search space?", "Medium"),
                _eval(6, "Implement Binary Search iteratively.", "Medium"),
            ]
            pc.return_value.process_answer = AsyncMock(side_effect=turn_returns)
            svc = InterviewService(MagicMock())

        repo = _mock_repo(interview, q1_msg)
        svc.repository = repo

        r1 = await svc.submit_answer(iid, "Binary Search halves a sorted array...")

        assert r1["next_question"] == "How does Binary Search reduce the search space?"
        assert r1["status"] == "active"

        # Turn 2: latest message now has answer + next_question
        q2_msg = SimpleNamespace(
            id=uuid4(),
            question="What is Binary Search, and why is it useful?",
            answer="Binary Search halves a sorted array...",
            score=8,
            next_question="How does Binary Search reduce the search space?",
        )
        repo.get_latest_message = AsyncMock(return_value=q2_msg)

        r2 = await svc.submit_answer(iid, "It compares with mid and eliminates half.")

        assert r2["next_question"] == "Implement Binary Search iteratively."
        assert r2["status"] == "active"

    @pytest.mark.asyncio
    async def test_no_duplicate_q1_records(self) -> None:
        """Answering updates the pending record, no new row for Q1."""
        iid = uuid4()
        interview = _make_interview(iid, max_questions=3)

        q1 = _pending_message("What is Binary Search?")

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(
                return_value=_eval(8, "Q2 about mechanism?", "Medium")
            )
            svc = InterviewService(MagicMock())

        repo = _mock_repo(interview, q1)
        svc.repository = repo

        await svc.submit_answer(iid, "A" * 50)

        repo.update_message.assert_awaited()
        repo.save_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_next_question_stored_on_answered_message(self) -> None:
        """next_question persisted on the same message record."""
        iid = uuid4()
        interview = _make_interview(iid, max_questions=5)

        q1 = _pending_message("What is Binary Search?")

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(
                return_value=_eval(8, "How does Binary Search work step by step?", "Hard")
            )
            svc = InterviewService(MagicMock())

        repo = _mock_repo(interview, q1)
        repo.update_message = AsyncMock(return_value=q1)
        svc.repository = repo

        await svc.submit_answer(iid, "A" * 50)

        # update_message called twice: once for answer+eval, once to store next_question
        assert repo.update_message.await_count == 2
        second_call = repo.update_message.call_args_list[1]
        assert second_call.args[0] == q1.id
        assert second_call.kwargs["next_question"] == "How does Binary Search work step by step?"


# ===========================================================================
# J. Question progression (concept deepening via fallback)
# ===========================================================================

class TestQuestionProgression:

    def test_fallback_starts_with_definition(self) -> None:
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Binary Search")
        q = ctrl.fallback("Medium", [])
        assert "What is" in q
        assert "Binary Search" in q

    def test_fallback_moves_past_covered_concepts(self) -> None:
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Binary Search")

        q1 = ctrl.fallback("Medium", [])
        q2 = ctrl.fallback("Medium", [q1])
        q3 = ctrl.fallback("Medium", [q1, q2])

        assert q1 != q2
        assert q2 != q3
        assert q1 != q3

    def test_fallback_covers_all_concepts(self) -> None:
        """Run fallback 5 times with growing history; all returned questions differ."""
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Binary Search")

        questions = []
        for _ in range(5):
            q = ctrl.fallback("Medium", questions)
            assert q not in questions, f"Repeated question: {q}"
            questions.append(q)

    def test_fallback_returns_generic_after_all_concepts(self) -> None:
        """After all 5 concepts are covered, fallback returns a generic question."""
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Binary Search")

        all_qs = []
        for _ in range(5):
            q = ctrl.fallback("Medium", all_qs)
            all_qs.append(q)

        generic = ctrl.fallback("Medium", all_qs)
        assert generic not in all_qs
        assert "Binary Search" in generic

    def test_fallback_all_questions_contain_topic(self) -> None:
        """Every fallback question must contain the topic."""
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Binary Search")

        questions = []
        for _ in range(6):
            q = ctrl.fallback("Medium", questions)
            assert "Binary Search" in q, f"Missing topic in: {q}"
            questions.append(q)

    def test_validate_catches_semantic_duplicates(self) -> None:
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Binary Search")

        valid, reason = ctrl.validate(
            "What is Binary Search and how does it work?",
            ["What is Binary Search and how does it work?"],
        )
        assert not valid
        assert reason == "duplicate"

    def test_validate_allows_progressively_deeper_questions(self) -> None:
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Binary Search")

        q1 = "What is Binary Search, and why is it useful?"
        q2 = "How does Binary Search reduce the search space at each step?"
        q3 = "When implementing Binary Search iteratively, what are the key operations?"

        valid1, _ = ctrl.validate(q1, [])
        assert valid1

        valid2, _ = ctrl.validate(q2, [q1])
        assert valid2

        valid3, _ = ctrl.validate(q3, [q1, q2])
        assert valid3

    def test_choose_focus_advances(self) -> None:
        from ai_engine.services.question_controller import AdaptiveQuestionController
        ctrl = AdaptiveQuestionController("Binary Search")

        assert ctrl.choose_focus("Medium", []) == "definition"
        assert ctrl.choose_focus("Medium", ["What is Binary Search?"]) == "mechanism"
        assert ctrl.choose_focus("Medium", [
            "What is Binary Search?", "How does Binary Search work?"
        ]) == "implementation"
