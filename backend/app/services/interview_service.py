"""
Service layer for interview business logic.
Orchestrates interactions between API layer, repositories, and AI provider.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AIProviderException,
    InterviewAlreadyEndedException,
    InterviewNotActiveException,
    InterviewNotFoundException,
    InvalidAnswerException,
)
from app.models.interview import Interview, InterviewStatus
from app.providers.ai_provider import AIProvider
from app.repositories.interview_repository import InterviewRepository
from app.utils.parser import format_evaluation_for_response, parse_evaluation


class InterviewService:
    """
    Service layer for interview operations.

    Coordinates between:
        - InterviewRepository (database CRUD)
        - AIProvider (question generation, answer evaluation)
        - API layer (request/response formatting)

    Contains all business logic for interview flow.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the service with required dependencies.

        Args:
            session: An async SQLAlchemy session.
        """
        self.repository = InterviewRepository(session)
        self.ai_provider = AIProvider()
        self.session = session

    async def start_interview(
        self,
        candidate_name: str,
        role: str,
        topic: str,
        difficulty: str = "Easy",
    ) -> Dict[str, Any]:
        """
        Start a new interview session.

        Creates the interview record in the database, generates the first
        question via the AI provider, and saves the initial message.

        Args:
            candidate_name: Name of the candidate.
            role: The job role.
            topic: The technical topic.
            difficulty: Starting difficulty level.

        Returns:
            A dictionary with interview_id, first question, and difficulty.

        Raises:
            AIProviderException: If the AI engine fails to generate a question.
        """
        # Create interview record
        interview = await self.repository.create_interview(
            candidate_name=candidate_name,
            role=role,
            topic=topic,
            difficulty=difficulty,
        )

        # Generate first question
        try:
            question = await self.ai_provider.generate_question(
                topic=topic,
                difficulty=difficulty,
            )
        except Exception as exc:
            raise AIProviderException(
                message=f"Failed to generate first question: {str(exc)}"
            ) from exc

        # Save initial message (question only, no answer yet)
        await self.repository.save_message(
            interview_id=interview.id,
            question=question,
        )

        return {
            "interview_id": str(interview.id),
            "question": question,
            "difficulty": difficulty,
        }

    async def submit_answer(
        self,
        interview_id: uuid.UUID,
        answer: str,
    ) -> Dict[str, Any]:
        """
        Submit an answer for evaluation and get the next question.

        Validates the interview state, saves the answer, evaluates it
        via the AI provider, adjusts difficulty based on score, and
        generates the next question.

        Args:
            interview_id: The UUID of the active interview.
            answer: The candidate's answer text.

        Returns:
            A dictionary with score, feedback, strengths, improvements,
            and next_question.

        Raises:
            InterviewNotFoundException: If the interview does not exist.
            InterviewNotActiveException: If the interview is not active.
            InterviewAlreadyEndedException: If the interview has ended.
            InvalidAnswerException: If the answer is too short.
            AIProviderException: If the AI engine fails.
        """
        # Validate answer length
        stripped_answer = answer.strip()
        if len(stripped_answer) < 10:
            raise InvalidAnswerException(
                "Answer must be at least 10 characters."
            )

        # Fetch interview
        interview = await self.repository.get_interview(interview_id)
        if interview is None:
            raise InterviewNotFoundException(str(interview_id))

        # Validate interview state
        if interview.status == InterviewStatus.COMPLETED:
            raise InterviewAlreadyEndedException(str(interview_id))
        if interview.status != InterviewStatus.ACTIVE:
            raise InterviewNotActiveException(str(interview_id))

        # Get the current question (latest message without an answer)
        latest_message = await self.repository.get_latest_message(interview_id)
        if latest_message is None or latest_message.answer is not None:
            current_question = latest_message.question if latest_message else ""
        else:
            current_question = latest_message.question

        # Evaluate answer via AI
        try:
            evaluation = await self.ai_provider.evaluate_answer(
                question=current_question,
                answer=stripped_answer,
            )
        except Exception as exc:
            raise AIProviderException(
                message=f"Failed to evaluate answer: {str(exc)}"
            ) from exc

        # Save the answer and evaluation
        await self.repository.save_message(
            interview_id=interview_id,
            question=evaluation.get("next_question", current_question),
            answer=stripped_answer,
            score=evaluation.get("score", 0),
            feedback=evaluation.get("feedback", ""),
            strengths=", ".join(evaluation.get("strengths", [])),
            improvements=", ".join(evaluation.get("improvements", [])),
            next_question=evaluation.get("next_question", ""),
        )

        # Adjust difficulty based on score
        score = evaluation.get("score", 0)
        new_difficulty = self._adjust_difficulty(score, interview.difficulty)
        if new_difficulty != interview.difficulty:
            await self.repository.update_interview_difficulty(
                interview_id, new_difficulty
            )

        # Format the response
        return format_evaluation_for_response(evaluation)

    async def end_interview(
        self,
        interview_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        End an interview session.

        Marks the interview as completed with an end timestamp.

        Args:
            interview_id: The UUID of the interview to end.

        Returns:
            A dictionary with confirmation status and interview_id.

        Raises:
            InterviewNotFoundException: If the interview does not exist.
            InterviewAlreadyEndedException: If already ended.
        """
        interview = await self.repository.finish_interview(interview_id)
        if interview is None:
            raise InterviewNotFoundException(str(interview_id))

        return {
            "status": "completed",
            "interview_id": str(interview.id),
        }

    async def get_interview(
        self,
        interview_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Get interview details including the current state.

        Args:
            interview_id: The UUID of the interview.

        Returns:
            A dictionary with interview details.

        Raises:
            InterviewNotFoundException: If the interview does not exist.
        """
        interview = await self.repository.get_interview_with_messages(interview_id)
        if interview is None:
            raise InterviewNotFoundException(str(interview_id))

        messages = interview.messages
        latest_message = messages[-1] if messages else None

        return {
            "interview_id": str(interview.id),
            "candidate_name": interview.candidate_name,
            "role": interview.role,
            "topic": interview.topic,
            "difficulty": interview.difficulty,
            "status": interview.status.value if interview.status else None,
            "started_at": interview.started_at.isoformat() if interview.started_at else None,
            "ended_at": interview.ended_at.isoformat() if interview.ended_at else None,
            "current_question": latest_message.question if latest_message else None,
            "total_questions": len(messages),
        }

    async def get_interview_history(
        self,
        interview_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Get the full interview history including all messages.

        Args:
            interview_id: The UUID of the interview.

        Returns:
            A dictionary with interview metadata and all Q&A messages.

        Raises:
            InterviewNotFoundException: If the interview does not exist.
        """
        interview = await self.repository.get_interview_with_messages(interview_id)
        if interview is None:
            raise InterviewNotFoundException(str(interview_id))

        messages = [
            {
                "id": str(msg.id),
                "interview_id": str(msg.interview_id),
                "question": msg.question,
                "answer": msg.answer,
                "score": msg.score,
                "feedback": msg.feedback,
                "strengths": msg.strengths,
                "improvements": msg.improvements,
                "next_question": msg.next_question,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in interview.messages
        ]

        return {
            "interview_id": str(interview.id),
            "candidate_name": interview.candidate_name,
            "role": interview.role,
            "topic": interview.topic,
            "difficulty": interview.difficulty,
            "status": interview.status.value if interview.status else None,
            "started_at": interview.started_at.isoformat() if interview.started_at else None,
            "ended_at": interview.ended_at.isoformat() if interview.ended_at else None,
            "messages": messages,
        }

    def _adjust_difficulty(self, score: int, current_difficulty: str) -> str:
        """
        Adjust difficulty based on performance score.

        Implements adaptive difficulty:
            - Score >= 8: Increase difficulty (Easy -> Medium -> Hard)
            - Score <= 4: Decrease difficulty (Hard -> Medium -> Easy)
            - Otherwise: Keep current difficulty

        Args:
            score: The evaluation score (0-10).
            current_difficulty: The current difficulty level.

        Returns:
            The adjusted difficulty level.
        """
        difficulty_order = ["Easy", "Medium", "Hard"]
        try:
            current_idx = difficulty_order.index(current_difficulty)
        except ValueError:
            current_idx = 0

        if score >= settings.SCORE_UPGRADE_THRESHOLD:
            new_idx = min(current_idx + 1, len(difficulty_order) - 1)
        elif score <= settings.SCORE_DOWNGRADE_THRESHOLD:
            new_idx = max(current_idx - 1, 0)
        else:
            new_idx = current_idx

        return difficulty_order[new_idx]
