"""
SQLAlchemy model for the interviews table.
Stores interview session metadata.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Enum as SQLEnum, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.message import InterviewMessage


class InterviewStatus(str, PyEnum):
    """Enum for interview session status values."""
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class Interview(Base):
    """
    Represents an interview session.

    Each interview belongs to one candidate and tracks the
    overall session state, difficulty, and timing.
    """

    __tablename__ = "interviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    candidate_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    topic: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    difficulty: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Easy",
    )
    status: Mapped[InterviewStatus] = mapped_column(
        SQLEnum(InterviewStatus, name="interview_status"),
        nullable=False,
        default=InterviewStatus.ACTIVE,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    messages: Mapped[List[InterviewMessage]] = relationship(
        "InterviewMessage",
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="InterviewMessage.created_at",
    )

    def __repr__(self) -> str:
        return (
            f"<Interview(id={self.id}, "
            f"candidate='{self.candidate_name}', "
            f"role='{self.role}', "
            f"topic='{self.topic}', "
            f"status='{self.status}')>"
        )

    def to_dict(self) -> dict:
        """Serialize interview to dictionary."""
        return {
            "id": str(self.id),
            "candidate_name": self.candidate_name,
            "role": self.role,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "status": self.status.value if self.status else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }
