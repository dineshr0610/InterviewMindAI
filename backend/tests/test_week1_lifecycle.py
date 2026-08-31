"""Regression tests for the Week 1 interview turn contract."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.interview import InterviewStatus
from app.services.interview_service import InterviewService


def _interview(interview_id, max_questions: int = 5, resume_text: str | None = None):
    return SimpleNamespace(
        id=interview_id,
        topic="Binary Search",
        difficulty="Medium",
        max_questions=max_questions,
        status=InterviewStatus.ACTIVE,
        resume_text=resume_text,
    )


def _evaluation(score: int = 8):
    return {
        "score": score,
        "feedback": "Clear explanation of the Binary Search invariant.",
        "strengths": ["Correctly reduces the search interval"],
        "improvements": ["Mention duplicate-value handling"],
    }


@pytest.mark.asyncio
async def test_answer_updates_pending_question_and_returns_next_question() -> None:
    """Q1 is updated in place; Q2 is stored as Q1's next_question."""
    interview_id = uuid4()
    q1 = SimpleNamespace(id=uuid4(), question="What is Binary Search?", answer=None)

    with patch("app.services.interview_service.AIProvider") as provider_class:
        provider = provider_class.return_value
        provider.process_answer = AsyncMock(
            return_value={
                **_evaluation(),
                "next_question": "How does Binary Search reduce the search space?",
                "difficulty": "Hard",
                "completed": False,
            }
        )
        service = InterviewService(MagicMock())

    repository = MagicMock()
    repository.get_interview = AsyncMock(return_value=_interview(interview_id))
    repository.get_latest_message = AsyncMock(return_value=q1)
    repository.update_message = AsyncMock(return_value=q1)
    repository.get_answered_message_count = AsyncMock(return_value=1)
    repository.get_messages = AsyncMock(return_value=[q1])
    repository.save_message = AsyncMock()
    repository.update_interview_difficulty = AsyncMock()
    service.repository = repository

    result = await service.submit_answer(
        interview_id,
        "Binary Search repeatedly compares the midpoint and discards the half that cannot contain the target.",
    )

    assert result["next_question"] == "How does Binary Search reduce the search space?"
    assert result["difficulty"] == "Hard"
    assert result["status"] == "active"
    repository.save_message.assert_not_awaited()
    assert repository.update_message.await_count == 2
    provider.process_answer.assert_awaited_once_with(
        question=q1.question,
        answer="Binary Search repeatedly compares the midpoint and discards the half that cannot contain the target.",
        topic="Binary Search",
        difficulty="Medium",
        history=[],
        question_number=0,
        max_questions=5,
        resume_text=None,
    )


@pytest.mark.asyncio
async def test_next_turn_creates_only_its_own_answered_record() -> None:
    """A stored next question becomes one Q&A record when it is answered."""
    interview_id = uuid4()
    q1 = SimpleNamespace(
        id=uuid4(),
        question="What is Binary Search?",
        answer="It searches sorted data by halving the remaining interval.",
        next_question="What invariant must Binary Search preserve?",
        score=8,
    )
    q2 = SimpleNamespace(id=uuid4(), question=q1.next_question, answer="A detailed answer", score=6)

    with patch("app.services.interview_service.AIProvider") as provider_class:
        provider = provider_class.return_value
        provider.process_answer = AsyncMock(
            return_value={
                **_evaluation(6),
                "next_question": "Which Binary Search edge cases require special handling?",
                "difficulty": "Medium",
                "completed": False,
            }
        )
        service = InterviewService(MagicMock())

    repository = MagicMock()
    repository.get_interview = AsyncMock(return_value=_interview(interview_id))
    repository.get_latest_message = AsyncMock(return_value=q1)
    repository.save_message = AsyncMock(return_value=q2)
    repository.update_message = AsyncMock(return_value=q2)
    repository.get_answered_message_count = AsyncMock(return_value=2)
    repository.get_messages = AsyncMock(return_value=[q1, q2])
    repository.update_interview_difficulty = AsyncMock()
    service.repository = repository

    await service.submit_answer(
        interview_id,
        "The invariant is that if the target exists, it remains within the inclusive low-to-high search interval.",
    )

    repository.save_message.assert_awaited_once()
    saved = repository.save_message.await_args.kwargs
    assert saved["question"] == q1.next_question
    assert saved["answer"].startswith("The invariant")
    assert repository.update_message.await_args.kwargs["next_question"].startswith("Which Binary Search")


@pytest.mark.asyncio
async def test_limit_completes_without_generating_or_accepting_another_question() -> None:
    """The final allowed answer completes the interview and has no next question."""
    interview_id = uuid4()
    q1 = SimpleNamespace(id=uuid4(), question="What is Binary Search?", answer=None)

    with patch("app.services.interview_service.AIProvider") as provider_class:
        provider = provider_class.return_value
        provider.process_answer = AsyncMock(
            return_value={
                **_evaluation(3),
                "next_question": None,
                "difficulty": "Easy",
                "completed": True,
            }
        )
        service = InterviewService(MagicMock())

    repository = MagicMock()
    repository.get_interview = AsyncMock(return_value=_interview(interview_id, max_questions=1))
    repository.get_latest_message = AsyncMock(return_value=q1)
    repository.update_message = AsyncMock(return_value=q1)
    repository.get_answered_message_count = AsyncMock(return_value=1)
    repository.get_messages = AsyncMock(return_value=[q1])
    repository.finish_interview = AsyncMock()
    repository.update_interview_difficulty = AsyncMock()
    service.repository = repository

    result = await service.submit_answer(
        interview_id,
        "Binary Search requires sorted data and halves the remaining candidate interval after each comparison.",
    )

    assert result["next_question"] is None
    assert result["status"] == "completed"
    repository.finish_interview.assert_awaited_once_with(interview_id)
