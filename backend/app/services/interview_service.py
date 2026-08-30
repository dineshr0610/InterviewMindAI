"""
Service layer for interview business logic.
Orchestrates interactions between API layer, repositories, and AI provider.
"""

from __future__ import annotations

import uuid
import logging
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

logger = logging.getLogger("interviewmind.services.interview")

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
        topic: Optional[str] = None,
        difficulty: str = "Easy",
        max_questions: int = settings.DEFAULT_MAX_QUESTIONS,
    ) -> Dict[str, Any]:
        """
        Start a new interview session.

        Creates the interview record in the database, generates the first
        question via the AI provider, and saves the initial message.

        Args:
            candidate_name: Name of the candidate.
            role: The job role.
            topic: The technical topic (defaults to role if omitted).
            difficulty: Starting difficulty level.
            max_questions: Maximum questions for this interview session.

        Returns:
            A dictionary with interview_id, first question, and difficulty.

        Raises:
            AIProviderException: If the AI engine fails to generate a question.
        """
        resolved_topic = (topic or "").strip() or (role or "").strip() or "General Technical"
        resolved_difficulty = difficulty or "Easy"
        resolved_max_questions = max_questions or settings.DEFAULT_MAX_QUESTIONS

        # Create interview record
        interview = await self.repository.create_interview(
            candidate_name=candidate_name.strip(),
            role=role.strip(),
            topic=resolved_topic,
            difficulty=resolved_difficulty,
            max_questions=resolved_max_questions,
        )

        # Generate first question
        try:
            question = await self.ai_provider.generate_question(
                topic=resolved_topic,
                difficulty=resolved_difficulty,
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

        # The only pending question is the latest message without an answer.
        # After it is answered, the next question is kept on that same record.
        latest_message = await self.repository.get_latest_message(interview_id)
        if latest_message is None:
            raise InterviewNotActiveException(str(interview_id))
        if latest_message.answer is None:
            current_question = latest_message.question
            pending_message = latest_message
        else:
            current_question = latest_message.next_question or ""
            pending_message = None

        if not current_question:
            raise InterviewNotActiveException(str(interview_id))

        messages = await self.repository.get_messages(interview_id)
        answered_count_before = sum(1 for message in messages if message.answer is not None)
        history = [
            {"question": message.question, "answer": message.answer, "score": message.score}
            for message in messages
            if message.answer is not None
        ]

        # The provider executes the protected LangGraph for this answer turn.
        try:
            evaluation = await self.ai_provider.process_answer(
                question=current_question,
                answer=stripped_answer,
                topic=interview.topic,
                difficulty=interview.difficulty,
                history=history,
                question_number=answered_count_before,
                max_questions=interview.max_questions,
            )
        except Exception as exc:
            raise AIProviderException(
                message=f"Failed to evaluate answer: {str(exc)}"
            ) from exc

        # Save the candidate answer against the actual current question.
        # Updating the pending record avoids duplicate question history rows.
        score = int(evaluation.get("score", 0) or 0)
        message_values = {
            "answer": stripped_answer,
            "score": score,
            "feedback": evaluation.get("feedback", ""),
            "strengths": ", ".join(evaluation.get("strengths", [])),
            "improvements": ", ".join(evaluation.get("improvements", [])),
        }
        if pending_message is not None:
            answered_message = await self.repository.update_message(
                pending_message.id,
                **message_values,
            )
        else:
            answered_message = await self.repository.save_message(
                interview_id=interview_id,
                question=current_question,
                **message_values,
            )

        # Adapt difficulty from the candidate's performance.
        new_difficulty = evaluation.get("difficulty") or self._adjust_difficulty(score, interview.difficulty)

        if new_difficulty != interview.difficulty:
            await self.repository.update_interview_difficulty(
                interview_id,
                new_difficulty,
            )

        answered_count = await self.repository.get_answered_message_count(interview_id)
        if answered_count >= interview.max_questions:
            await self.repository.finish_interview(interview_id)
            evaluation.update(
                next_question=None,
                difficulty=new_difficulty,
                status=InterviewStatus.COMPLETED.value,
            )
            return format_evaluation_for_response(evaluation)

        next_question = evaluation.get("next_question")
        if not next_question and answered_count < interview.max_questions:
            try:
                previous_questions = [msg.question for msg in messages if msg.question]
                next_question = await self.ai_provider.generate_question(
                    topic=interview.topic,
                    difficulty=new_difficulty,
                    previous_questions=previous_questions,
                )
            except Exception as e:
                logger.warning("Failed to generate fallback next question: %s", e)
                next_question = None

        if not next_question:
            await self.repository.finish_interview(interview_id)
            evaluation.update(
                next_question=None,
                difficulty=new_difficulty,
                status=InterviewStatus.COMPLETED.value,
            )
            return format_evaluation_for_response(evaluation)

        # Keep the next question on the just-answered message. The next turn
        # creates its own message only when it receives an answer.
        await self.repository.update_message(
            answered_message.id,
            next_question=next_question,
        )

        evaluation.update(
            next_question=next_question,
            difficulty=new_difficulty,
            status=InterviewStatus.ACTIVE.value,
        )

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
            "max_questions": interview.max_questions,
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
            "max_questions": interview.max_questions,
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





