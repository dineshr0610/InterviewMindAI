"""
Interview API routes.
Handles all interview lifecycle operations: start, answer, get details, history, end.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.schemas.interview import (
    AnswerRequest,
    StartInterviewRequest,
)
from app.services.interview_service import InterviewService
from app.utils.response import success_response

logger = logging.getLogger("interviewmind.routes.interview")
router = APIRouter(prefix="/api/interview", tags=["Interview"])


async def get_interview_service(
    db: AsyncSession = Depends(get_db_session),
) -> InterviewService:
    """Dependency that creates an InterviewService instance with an active DB session."""
    return InterviewService(session=db)


@router.post(
    "/start",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new interview",
    description="Creates a new interview session and returns the initial question.",
)
async def start_interview(
    request: StartInterviewRequest,
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    """Start a new mock interview session."""
    result = await service.start_interview(
        candidate_name=request.candidate_name,
        role=request.role,
        topic=request.topic,
    )
    logger.info(
        "Interview started: id=%s, candidate=%s, role=%s, topic=%s",
        result.get("interview_id"),
        request.candidate_name,
        request.role,
        request.topic,
    )
    return success_response(result, status_code=status.HTTP_201_CREATED)


@router.post(
    "/answer",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Submit an answer and get evaluation",
    description="Submit an answer for evaluation and receive score, feedback, and the next question.",
)
async def submit_answer(
    request: AnswerRequest,
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    """Submit an answer for AI evaluation and receive follow-up question."""
    result = await service.submit_answer(
        interview_id=request.interview_id,
        answer=request.answer,
    )
    logger.info(
        "Answer evaluated: interview_id=%s, score=%d",
        request.interview_id,
        result.get("score", 0),
    )
    return success_response(result)


@router.get(
    "/{interview_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get interview details",
    description="Retrieve status and current state of a specific interview session by ID.",
)
async def get_interview(
    interview_id: UUID = Path(..., description="UUID of the interview session"),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    """Get interview details by ID."""
    result = await service.get_interview(interview_id=interview_id)
    return success_response(result)


@router.get(
    "/{interview_id}/history",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get interview history",
    description="Retrieve the complete transcript of Q&As for a specific interview session.",
)
async def get_interview_history(
    interview_id: UUID = Path(..., description="UUID of the interview session"),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    """Get full interview Q&A history transcript."""
    result = await service.get_interview_history(interview_id=interview_id)
    return success_response(result)


@router.post(
    "/{interview_id}/end",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="End an interview",
    description="Conclude an active interview session.",
)
async def end_interview(
    interview_id: UUID = Path(..., description="UUID of the interview session to end"),
    service: InterviewService = Depends(get_interview_service),
) -> dict:
    """End an active interview session."""
    result = await service.end_interview(interview_id=interview_id)
    logger.info("Interview ended: id=%s", interview_id)
    return success_response(result)
