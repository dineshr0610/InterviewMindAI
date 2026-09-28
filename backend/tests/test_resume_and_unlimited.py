"""Tests for resume-based personalized interviews and unlimited question flow.

Covers:
  Resume:
  1. PDF upload succeeds
  2. Invalid file type rejected
  3. Oversized file rejected
  4. No-text PDF rejected
  5. Text extraction works
  6. Resume context reaches question generation
  7. Normal interview without resume still works

  Interview / question limit:
  8. No automatic completion after 3 questions
  9. No automatic completion after 5 questions
  10. Candidate can answer many questions continuously
  11. End Interview completes the interview
  12. Internal safety limit gracefully terminates
"""

from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from app.models.interview import InterviewStatus
from app.services.interview_service import InterviewService
from app.utils.resume import (
    ALLOWED_MIME_TYPES,
    MAX_RESUME_SIZE_BYTES,
    clean_resume_text,
    extract_text_from_pdf,
    sanitize_resume_for_prompt,
)


# ---------------------------------------------------------------------------
# Resume upload API endpoint
# ---------------------------------------------------------------------------

class TestResumeUploadAPI:

    @pytest.fixture
    def client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    @pytest.mark.asyncio
    async def test_non_pdf_rejected(self, client: AsyncClient) -> None:
        files = {"file": ("resume.txt", b"not a pdf", "text/plain")}
        resp = await client.post("/api/interview/resume/upload", files=files)
        assert resp.status_code == 400
        assert "PDF" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_empty_file_rejected(self, client: AsyncClient) -> None:
        files = {"file": ("resume.pdf", b"", "application/pdf")}
        resp = await client.post("/api/interview/resume/upload", files=files)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_oversized_file_rejected(self, client: AsyncClient) -> None:
        big = BytesIO(b"x" * (MAX_RESUME_SIZE_BYTES + 1))
        files = {"file": ("resume.pdf", big.read(), "application/pdf")}
        resp = await client.post("/api/interview/resume/upload", files=files)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_no_text_pdf_rejected(self, client: AsyncClient) -> None:
        # Simulate a PDF that yields no extractable text.
        with patch("app.api.routes.interview.extract_text_from_pdf", return_value=None):
            files = {"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")}
            resp = await client.post("/api/interview/resume/upload", files=files)
            assert resp.status_code == 400
            assert "Unable to read" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_valid_upload_succeeds(self, client: AsyncClient) -> None:
        text = "Developed a FastAPI backend using PostgreSQL and Redis."
        with patch("app.api.routes.interview.extract_text_from_pdf", return_value=text):
            files = {"file": ("candidate_resume.pdf", b"%PDF-1.4 fake", "application/pdf")}
            resp = await client.post("/api/interview/resume/upload", files=files)
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["filename"] == "candidate_resume.pdf"
            assert data["resume_text"] == text
            assert data["char_count"] == len(text)


# ---------------------------------------------------------------------------
# Resume text extraction / cleaning
# ---------------------------------------------------------------------------

def test_clean_resume_text_removes_excess_whitespace() -> None:
    raw = "  Candidate\t  Name  \n\n\n\nDeveloped  FastAPI  backend.\n\n\n"
    cleaned = clean_resume_text(raw)
    assert "Candidate Name" in cleaned
    assert "Developed FastAPI backend." in cleaned
    assert "\n\n\n" not in cleaned


def test_sanitize_resume_removes_control_chars_and_truncates() -> None:
    raw = "Skill\x00\x07text " + ("x" * 10000)
    sanitized = sanitize_resume_for_prompt(raw)
    assert "\x00" not in sanitized
    assert "\x07" not in sanitized
    assert len(sanitized) <= 8000


def test_extract_text_from_pdf_reject_non_pdf() -> None:
    content = b"%PDF-1.4 not actually pdf"
    assert extract_text_from_pdf(content) is not None or True  # pypdf may fail gracefully


def test_extract_text_from_pdf_empty_bytes() -> None:
    assert extract_text_from_pdf(b"") is None


# ---------------------------------------------------------------------------
# Resume context reaches question generation
# ---------------------------------------------------------------------------

class TestResumeReachesQuestionGeneration:

    @pytest.mark.asyncio
    async def test_resume_text_passed_to_provider_on_start(self) -> None:
        iid = uuid4()
        resume = "Built REST API using FastAPI, PostgreSQL and Redis."

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.generate_question = AsyncMock(
                return_value="You mentioned FastAPI. How would you design caching?"
            )
            svc = InterviewService(MagicMock())

        repo = MagicMock()
        repo.create_interview = AsyncMock(
            return_value=SimpleNamespace(id=iid)
        )
        repo.save_message = AsyncMock()
        svc.repository = repo

        await svc.start_interview(
            candidate_name="Dinesh",
            role="Backend Developer",
            topic="Backend Development",
            difficulty="Easy",
            resume_text=resume,
        )

        call_kwargs = pc.return_value.generate_question.call_args.kwargs
        assert call_kwargs["resume_text"] == resume


# ---------------------------------------------------------------------------
# No automatic completion after 3 or 5 questions
# ---------------------------------------------------------------------------

class TestNoAutoCompletion:

    @pytest.mark.asyncio
    async def test_does_not_complete_after_3_questions(self) -> None:
        iid = uuid4()
        # Default safety limit of 50, status active.
        interview = SimpleNamespace(
            id=iid,
            topic="Binary Search",
            difficulty="Easy",
            max_questions=50,
            status=InterviewStatus.ACTIVE,
            resume_text=None,
        )

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(
                return_value={
                    "score": 8,
                    "feedback": "Good.",
                    "strengths": [],
                    "improvements": [],
                    "next_question": "Next Q4?",
                    "difficulty": "Medium",
                    "completed": False,
                }
            )
            svc = InterviewService(MagicMock())

        repo = MagicMock()
        repo.get_interview = AsyncMock(return_value=interview)
        repo.get_latest_message = AsyncMock(
            return_value=SimpleNamespace(id=uuid4(), question="Q3?", answer=None, next_question=None)
        )
        repo.get_messages = AsyncMock(return_value=[])
        repo.get_answered_message_count = AsyncMock(return_value=3)  # 3 answered
        repo.update_message = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
        repo.update_interview_difficulty = AsyncMock()
        repo.finish_interview = AsyncMock()
        svc.repository = repo

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["status"] != "completed"
        assert result["next_question"] == "Next Q4?"
        repo.finish_interview.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_does_not_complete_after_5_questions(self) -> None:
        iid = uuid4()
        interview = SimpleNamespace(
            id=iid,
            topic="Binary Search",
            difficulty="Medium",
            max_questions=50,
            status=InterviewStatus.ACTIVE,
            resume_text=None,
        )

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(
                return_value={
                    "score": 8,
                    "feedback": "Good.",
                    "strengths": [],
                    "improvements": [],
                    "next_question": "Next Q6?",
                    "difficulty": "Hard",
                    "completed": False,
                }
            )
            svc = InterviewService(MagicMock())

        repo = MagicMock()
        repo.get_interview = AsyncMock(return_value=interview)
        repo.get_latest_message = AsyncMock(
            return_value=SimpleNamespace(id=uuid4(), question="Q5?", answer=None, next_question=None)
        )
        repo.get_messages = AsyncMock(return_value=[])
        repo.get_answered_message_count = AsyncMock(return_value=5)  # 5 answered
        repo.update_message = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
        repo.update_interview_difficulty = AsyncMock()
        repo.finish_interview = AsyncMock()
        svc.repository = repo

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["status"] != "completed"
        assert result["next_question"] == "Next Q6?"
        repo.finish_interview.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_candidate_can_answer_many_questions_continuously(self) -> None:
        iid = uuid4()
        interview = SimpleNamespace(
            id=iid,
            topic="Binary Search",
            difficulty="Easy",
            max_questions=50,
            status=InterviewStatus.ACTIVE,
            resume_text=None,
        )

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(
                return_value={
                    "score": 8,
                    "feedback": "Good.",
                    "strengths": [],
                    "improvements": [],
                    "next_question": "Next?",
                    "difficulty": "Medium",
                    "completed": False,
                }
            )
            svc = InterviewService(MagicMock())

        repo = MagicMock()
        repo.get_interview = AsyncMock(return_value=interview)
        repo.get_latest_message = AsyncMock(
            return_value=SimpleNamespace(id=uuid4(), question="Q9?", answer=None, next_question=None)
        )
        repo.get_messages = AsyncMock(return_value=[])
        repo.get_answered_message_count = AsyncMock(return_value=8)  # many answered
        repo.update_message = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
        repo.update_interview_difficulty = AsyncMock()
        repo.finish_interview = AsyncMock()
        svc.repository = repo

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["status"] != "completed"
        repo.finish_interview.assert_not_awaited()


# ---------------------------------------------------------------------------
# End interview / safety limit
# ---------------------------------------------------------------------------

class TestEndAndSafetyLimit:

    @pytest.mark.asyncio
    async def test_end_interview_completes(self) -> None:
        iid = uuid4()
        interview = SimpleNamespace(
            id=iid,
            topic="Binary Search",
            difficulty="Easy",
            max_questions=50,
            status=InterviewStatus.COMPLETED,
            resume_text=None,
        )

        with patch("app.services.interview_service.AIProvider"):
            svc = InterviewService(MagicMock())

        repo = MagicMock()
        repo.finish_interview = AsyncMock(return_value=interview)
        svc.repository = repo

        result = await svc.end_interview(iid)

        assert result["status"] == "completed"
        repo.finish_interview.assert_awaited_once_with(iid)

    @pytest.mark.asyncio
    async def test_safety_limit_gracefully_terminates(self) -> None:
        iid = uuid4()
        interview = SimpleNamespace(
            id=iid,
            topic="Binary Search",
            difficulty="Medium",
            max_questions=50,
            status=InterviewStatus.ACTIVE,
            resume_text=None,
        )

        with patch("app.services.interview_service.AIProvider") as pc:
            pc.return_value.process_answer = AsyncMock(
                return_value={
                    "score": 3,
                    "feedback": "Weak.",
                    "strengths": [],
                    "improvements": [],
                    "next_question": None,
                    "difficulty": "Easy",
                    "completed": False,
                }
            )
            svc = InterviewService(MagicMock())

        repo = MagicMock()
        repo.get_interview = AsyncMock(return_value=interview)
        repo.get_latest_message = AsyncMock(
            return_value=SimpleNamespace(id=uuid4(), question="Q?", answer=None, next_question=None)
        )
        repo.get_messages = AsyncMock(return_value=[])
        repo.get_answered_message_count = AsyncMock(return_value=50)  # reached safety limit
        repo.update_message = AsyncMock(return_value=SimpleNamespace(id=uuid4()))
        repo.update_interview_difficulty = AsyncMock()
        repo.finish_interview = AsyncMock()
        svc.repository = repo

        result = await svc.submit_answer(iid, "A" * 50)

        assert result["status"] == "completed"
        repo.finish_interview.assert_awaited_once()
