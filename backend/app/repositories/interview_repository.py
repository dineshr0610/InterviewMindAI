"""
Repository layer for interview data access.
Performs ONLY CRUD operations â€” no AI logic, no business rules.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.code_submission import CodeSubmission
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
        max_questions: int = 50,
        resume_text: Optional[str] = None,
        phase: str = "technical",
        candidate_profile: Optional[dict] = None,
        role_snapshot: Optional[dict] = None,
        resume_match: Optional[dict] = None,
        assessment_state: Optional[dict] = None,
    ) -> Interview:
        """
        Create a new interview session.

        Args:
            candidate_name: Name of the candidate.
            role: The job role.
            topic: The technical topic.
            difficulty: Starting difficulty level.
            max_questions: Internal safety limit for questions.
            resume_text: Cleaned resume text for personalized questions (optional).

        Returns:
            The created Interview instance.
        """
        interview = Interview(
            candidate_name=candidate_name,
            role=role,
            topic=topic,
            difficulty=difficulty,
            max_questions=max_questions,
            resume_text=resume_text,
            phase=phase,
            candidate_profile=candidate_profile,
            role_snapshot=role_snapshot,
            resume_match=resume_match,
            assessment_state=assessment_state,
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

    async def get_message_by_fingerprint(
        self,
        interview_id: uuid.UUID,
        fingerprint: str,
    ) -> Optional[InterviewMessage]:
        """Find an answer submission by its idempotency fingerprint."""
        stmt = (
            select(InterviewMessage)
            .where(
                InterviewMessage.interview_id == interview_id,
                InterviewMessage.answer_fingerprint == fingerprint,
            )
            .order_by(InterviewMessage.created_at.desc())
            .limit(1)
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

    async def update_interview_fields(
        self,
        interview_id: uuid.UUID,
        **fields,
    ) -> Optional[Interview]:
        interview = await self.get_interview(interview_id)
        if interview is None:
            return None
        for key, value in fields.items():
            if hasattr(interview, key):
                setattr(interview, key, value)
        await self.session.flush()
        return interview

    async def list_completed_by_candidate(
        self,
        candidate_name: str,
        exclude_id: Optional[uuid.UUID] = None,
    ) -> List[Interview]:
        stmt = (
            select(Interview)
            .where(
                Interview.candidate_name == candidate_name,
                Interview.status == InterviewStatus.COMPLETED,
                Interview.final_assessment.isnot(None),
            )
            .order_by(Interview.started_at.desc())
        )
        if exclude_id is not None:
            stmt = stmt.where(Interview.id != exclude_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

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
        topic: Optional[str] = None,
        question_difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        technical_concept: Optional[str] = None,
        technical_evaluation: Optional[dict] = None,
        communication_evaluation: Optional[dict] = None,
        answer_fingerprint: Optional[str] = None,
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
            topic=topic,
            question_difficulty=question_difficulty,
            question_type=question_type,
            technical_concept=technical_concept,
            technical_evaluation=technical_evaluation,
            communication_evaluation=communication_evaluation,
            answer_fingerprint=answer_fingerprint,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def update_message(
        self,
        message_id: uuid.UUID,
        answer: Optional[str] = None,
        score: Optional[int] = None,
        feedback: Optional[str] = None,
        strengths: Optional[str] = None,
        improvements: Optional[str] = None,
        next_question: Optional[str] = None,
        topic: Optional[str] = None,
        question_difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        technical_concept: Optional[str] = None,
        technical_evaluation: Optional[dict] = None,
        communication_evaluation: Optional[dict] = None,
        answer_fingerprint: Optional[str] = None,
    ) -> Optional[InterviewMessage]:
        message = await self.session.get(InterviewMessage, message_id)
        if message is None:
            return None

        if answer is not None:
            message.answer = answer
        if score is not None:
            message.score = score
        if feedback is not None:
            message.feedback = feedback
        if strengths is not None:
            message.strengths = strengths
        if improvements is not None:
            message.improvements = improvements
        if next_question is not None:
            message.next_question = next_question
        if topic is not None:
            message.topic = topic
        if question_difficulty is not None:
            message.question_difficulty = question_difficulty
        if question_type is not None:
            message.question_type = question_type
        if technical_concept is not None:
            message.technical_concept = technical_concept
        if technical_evaluation is not None:
            message.technical_evaluation = technical_evaluation
        if communication_evaluation is not None:
            message.communication_evaluation = communication_evaluation
        if answer_fingerprint is not None:
            message.answer_fingerprint = answer_fingerprint

        await self.session.flush()
        return message

    async def claim_pending_message(
        self,
        message_id: uuid.UUID,
        answer: str,
        fingerprint: str,
    ) -> Optional[InterviewMessage]:
        """Atomically claim an unanswered message so retries cannot double-evaluate."""
        from sqlalchemy import update as sql_update

        stmt = (
            sql_update(InterviewMessage)
            .where(
                InterviewMessage.id == message_id,
                InterviewMessage.answer.is_(None),
            )
            .values(answer=answer, answer_fingerprint=fingerprint)
            .returning(InterviewMessage.id)
        )
        result = await self.session.execute(stmt)
        claimed = result.first()
        await self.session.flush()
        if claimed is None:
            return None
        return await self.session.get(InterviewMessage, message_id)

    async def release_pending_message(
        self,
        message_id: uuid.UUID,
        fingerprint: str,
    ) -> bool:
        """Release an answer claim after an upstream evaluation failure.

        The conditional update prevents a failed request from clearing a newer
        submission. It makes a transient AI outage safely retryable.
        """
        from sqlalchemy import update as sql_update

        stmt = (
            sql_update(InterviewMessage)
            .where(
                InterviewMessage.id == message_id,
                InterviewMessage.answer_fingerprint == fingerprint,
                InterviewMessage.technical_evaluation.is_(None),
            )
            .values(answer=None, answer_fingerprint=None)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return bool(result.rowcount)
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

    async def get_answered_message_count(self, interview_id: uuid.UUID) -> int:
        """
        Get the count of answered messages for an interview.

        Args:
            interview_id: The UUID of the interview.

        Returns:
            The count of answered messages.
        """
        stmt = (
            select(InterviewMessage)
            .where(
                InterviewMessage.interview_id == interview_id,
                InterviewMessage.answer.isnot(None),
            )
        )
        result = await self.session.execute(stmt)
        return len(list(result.scalars().all()))

    # ------------------------------------------------------------------
    # Coding submission CRUD
    # ------------------------------------------------------------------

    async def save_code_submission(
        self,
        interview_id: uuid.UUID,
        problem_id: str,
        language: str,
        source_code: str,
        result: Optional[dict] = None,
    ) -> CodeSubmission:
        submission = CodeSubmission(
            interview_id=interview_id,
            problem_id=problem_id,
            language=language,
            source_code=source_code,
            result=result,
        )
        self.session.add(submission)
        await self.session.flush()
        return submission

    async def list_code_submissions(
        self,
        interview_id: uuid.UUID,
    ) -> List[CodeSubmission]:
        stmt = (
            select(CodeSubmission)
            .where(CodeSubmission.interview_id == interview_id)
            .order_by(CodeSubmission.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


