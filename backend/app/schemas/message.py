"""
Pydantic schemas for message-related API responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """
    Response schema for a single Q&A message.

    Attributes:
        id: The UUID of the message.
        interview_id: The UUID of the parent interview.
        question: The question that was asked.
        answer: The candidate's answer.
        score: The evaluation score (0-10).
        feedback: Detailed feedback on the answer.
        strengths: Identified strengths.
        improvements: Areas for improvement.
        next_question: The follow-up question.
        created_at: Timestamp of creation.
    """

    id: UUID = Field(
        ...,
        description="UUID of the message",
    )
    interview_id: UUID = Field(
        ...,
        description="UUID of the parent interview",
    )
    question: str = Field(
        ...,
        description="The question that was asked",
    )
    answer: Optional[str] = Field(
        None,
        description="The candidate's answer",
    )
    score: Optional[int] = Field(
        None,
        ge=0,
        le=10,
        description="Evaluation score out of 10",
    )
    feedback: Optional[str] = Field(
        None,
        description="Detailed feedback on the answer",
    )
    strengths: Optional[str] = Field(
        None,
        description="Identified strengths",
    )
    improvements: Optional[str] = Field(
        None,
        description="Areas for improvement",
    )
    next_question: Optional[str] = Field(
        None,
        description="The follow-up question",
    )
    created_at: Optional[datetime] = Field(
        None,
        description="Timestamp of creation",
    )


class MessageListResponse(BaseModel):
    """
    Response schema for a list of messages.

    Attributes:
        messages: List of message response objects.
        total: Total number of messages.
    """

    messages: list[MessageResponse] = Field(
        default_factory=list,
        description="List of Q&A messages",
    )
    total: int = Field(
        default=0,
        description="Total number of messages",
    )
