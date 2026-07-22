"""
Integration tests for Interview API routes and Service layer.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture
def client() -> AsyncClient:
    """Create an async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_start_interview_flow(client: AsyncClient) -> None:
    """Test POST /api/interview/start route."""
    payload = {
        "candidate_name": "Test Candidate",
        "role": "Backend Engineer",
        "topic": "Python FastAPI",
    }
    
    mock_service_res = {
        "interview_id": "123e4567-e89b-12d3-a456-426614174000",
        "question": "Explain FastAPI dependency injection.",
        "difficulty": "Easy",
    }

    with patch("app.services.interview_service.InterviewService.start_interview", new_callable=AsyncMock) as mock_start:
        mock_start.return_value = mock_service_res
        response = await client.post("/api/interview/start", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["interview_id"] == "123e4567-e89b-12d3-a456-426614174000"
        assert data["data"]["question"] == "Explain FastAPI dependency injection."


@pytest.mark.asyncio
async def test_submit_answer_flow(client: AsyncClient) -> None:
    """Test POST /api/interview/answer route."""
    payload = {
        "interview_id": "123e4567-e89b-12d3-a456-426614174000",
        "answer": "FastAPI uses Depends() for dependency injection which manages lifespan and sessions.",
    }

    mock_eval_res = {
        "score": 8,
        "feedback": "Great understanding of FastAPI dependency injection.",
        "strengths": ["Clear explanation", "Mentioned Depends"],
        "improvements": ["Elaborate on yield generator dependencies"],
        "next_question": "How do background tasks work in FastAPI?",
    }

    with patch("app.services.interview_service.InterviewService.submit_answer", new_callable=AsyncMock) as mock_answer:
        mock_answer.return_value = mock_eval_res
        response = await client.post("/api/interview/answer", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["score"] == 8
        assert data["data"]["next_question"] == "How do background tasks work in FastAPI?"


@pytest.mark.asyncio
async def test_get_history_flow(client: AsyncClient) -> None:
    """Test GET /api/interview/{id}/history route."""
    mock_history_res = {
        "interview_id": "123e4567-e89b-12d3-a456-426614174000",
        "candidate_name": "Test Candidate",
        "role": "Backend Engineer",
        "topic": "Python FastAPI",
        "messages": [
            {
                "question": "Explain FastAPI dependency injection.",
                "answer": "FastAPI uses Depends() for dependency injection.",
                "score": 8,
            }
        ]
    }

    with patch("app.services.interview_service.InterviewService.get_interview_history", new_callable=AsyncMock) as mock_hist:
        mock_hist.return_value = mock_history_res
        response = await client.get("/api/interview/123e4567-e89b-12d3-a456-426614174000/history")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["messages"]) == 1


@pytest.mark.asyncio
async def test_end_interview_flow(client: AsyncClient) -> None:
    """Test POST /api/interview/{id}/end route."""
    mock_end_res = {
        "status": "completed",
        "interview_id": "123e4567-e89b-12d3-a456-426614174000",
    }

    with patch("app.services.interview_service.InterviewService.end_interview", new_callable=AsyncMock) as mock_end:
        mock_end.return_value = mock_end_res
        response = await client.post("/api/interview/123e4567-e89b-12d3-a456-426614174000/end")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "completed"
