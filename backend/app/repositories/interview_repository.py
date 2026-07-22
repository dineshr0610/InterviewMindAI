"""
Repository layer for interview data access.
Performs ONLY CRUD operations — no AI logic, no business rules.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.interview import Interview, InterviewStatus
from app.models.message import InterviewMessage


class InterviewRepository:
    """
    Repository for Interview and InterviewMessage CRUD operations.
    All database access for interviews goes through this class.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the repository with a database session.

        Args:
            session: An async SQLAlchemy session.
        """
        self.session = session

    # ------------------------------------------------------------------
    # Interview CRUD
    # ------------------------------------------------------------------

    async def create_interview(
        self,
        candidate_name: str,
        role: str,
        topic: str,
        difficulty: str = "Easy",
    ) -> Interview:
        """
        Create a new interview session.

        Args:
            candidate_name: Name of the candidate.
            role: The job role.
            topic: The technical topic.
            difficulty: Starting difficulty level.

        Returns:
            The created Interview instance.
        """
        interview = Interview(
            candidate_name=candidate_name,
            role=role,
            topic=topic,
            difficulty=difficulty,
            status=InterviewStatus.ACTIVE,
        )
        self.session.add(interview)
        await self.session.flush()
        return interview

    async def get_interview(self, interview_id: uuid.UUID) -> Optional[Interview]:
        """
        Get an interview by its ID.

        Args:
            interview_id: The UUID of the interview.

        Returns:
            The Interview instance if found, None otherwise.
        """
        stmt = select(Interview).where(Interview.id == interview_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_interview_with_messages(
        self, interview_id: uuid.UUID
    ) -> Optional[Interview]:
        """
        Get an interview with all its messages eagerly loaded.

        Args:
            interview_id: The UUID of the interview.

        Returns:
            The Interview instance with messages if found, None otherwise.
        """
        stmt = (
            select(Interview)
            .where(Interview.id == interview_id)
            .options(selectinload(Interview.messages))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_interview_status(
        self,
        interview_id: uuid.UUID,
        status: InterviewStatus,
    ) -> Optional[Interview]:
        """
        Update the status of an interview.

        Args:
            interview_id: The UUID of the interview.
            status: The new status value.

        Returns:
            The updated Interview instance if found, None otherwise.
        """
        interview = await self.get_interview(interview_id)
        if interview is None:
            return None

        interview.status = status
        await self.session.flush()
        return interview

    async def finish_interview(self, interview_id: uuid.UUID) -> Optional[Interview]:
        """
        Mark an interview as completed with an end timestamp.

        Args:
            interview_id: The UUID of the interview.

        Returns:
            The updated Interview instance if found, None otherwise.
        """
        interview = await self.get_interview(interview_id)
        if interview is None:
            return None

        interview.status = InterviewStatus.COMPLETED
        interview.ended_at = datetime.now(timezone.utc)
        await self.session.flush()
        return interview

    async def update_interview_difficulty(
        self,
        interview_id: uuid.UUID,
        difficulty: str,
    ) -> Optional[Interview]:
        """
        Update the difficulty level of an interview.

        Args:
            interview_id: The UUID of the interview.
            difficulty: The new difficulty level.

        Returns:
            The updated Interview instance if found, None otherwise.
        """
        interview = await self.get_interview(interview_id)
        if interview is None:
            return None

        interview.difficulty = difficulty
        await self.session.flush()
        return interview

    # ------------------------------------------------------------------
    # Message CRUD
    # ------------------------------------------------------------------

    async def save_message(
        self,
        interview_id: uuid.UUID,
        question: str,
        answer: Optional[str] = None,
        score: Optional[int] = None,
        feedback: Optional[str] = None,
        strengths: Optional[str] = None,
        improvements: Optional[str] = None,
        next_question: Optional[str] = None,
    ) -> InterviewMessage:
        """
        Save a new Q&A message for an interview.

        Args:
            interview_id: The UUID of the parent interview.
            question: The question text.
            answer: The candidate's answer (optional, may be None for first question).
            score: Evaluation score (optional).
            feedback: Evaluation feedback (optional).
            strengths: Identified strengths (optional).
            improvements: Areas for improvement (optional).
            next_question: The next question (optional).

        Returns:
            The created InterviewMessage instance.
        """
        message = InterviewMessage(
            interview_id=interview_id,
            question=question,
            answer=answer,
            score=score,
            feedback=feedback,
            strengths=strengths,
            improvements=improvements,
            next_question=next_question,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def get_messages(
        self, interview_id: uuid.UUID
    ) -> List[InterviewMessage]:
        """
        Get all messages for an interview, ordered by creation time.

        Args:
            interview_id: The UUID of the interview.

        Returns:
            A list of InterviewMessage instances.
        """
        stmt = (
            select(InterviewMessage)
            .where(InterviewMessage.interview_id == interview_id)
            .order_by(InterviewMessage.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_message(
        self, interview_id: uuid.UUID
    ) -> Optional[InterviewMessage]:
        """
        Get the most recent message for an interview.

        Args:
            interview_id: The UUID of the interview.

        Returns:
            The latest InterviewMessage if any exist, None otherwise.
        """
        stmt = (
            select(InterviewMessage)
            .where(InterviewMessage.interview_id == interview_id)
            .order_by(InterviewMessage.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_message_count(self, interview_id: uuid.UUID) -> int:
        """
        Get the total number of messages for an interview.

        Args:
            interview_id: The UUID of the interview.

        Returns:
            The count of messages.
        """
        stmt = (
            select(InterviewMessage)
            .where(InterviewMessage.interview_id == interview_id)
        )
        result = await self.session.execute(stmt)
        return len(list(result.scalars().all()))
