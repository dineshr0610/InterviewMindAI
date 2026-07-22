"""
SQLAlchemy model for the interview_messages table.
Stores each Q&A turn within an interview session.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.interview import Interview


class InterviewMessage(Base):
    """
    Represents a single Q&A turn in an interview.

    Each message belongs to one interview and stores the
    question, answer, evaluation data, and next question.
    """

    __tablename__ = "interview_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    answer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    strengths: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    improvements: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    next_question: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    interview: Mapped[Interview] = relationship(
        "Interview",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return (
            f"<InterviewMessage(id={self.id}, "
            f"interview_id={self.interview_id}, "
            f"score={self.score})>"
        )

    def to_dict(self) -> dict:
        """Serialize message to dictionary."""
        return {
            "id": str(self.id),
            "interview_id": str(self.interview_id),
            "question": self.question,
            "answer": self.answer,
            "score": self.score,
            "feedback": self.feedback,
            "strengths": self.strengths,
            "improvements": self.improvements,
            "next_question": self.next_question,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
