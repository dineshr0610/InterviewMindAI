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
        max_questions: int = 5,
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
            max_questions=max_questions,
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
                topic=interview.topic,
                difficulty=interview.difficulty,
            )
        except Exception as exc:
            raise AIProviderException(
                message=f"Failed to evaluate answer: {str(exc)}"
            ) from exc

        # Save the candidate answer against the ACTUAL current question.
        score = int(evaluation.get("score", 0) or 0)

        await self.repository.save_message(
            interview_id=interview_id,
            question=current_question,
            answer=stripped_answer,
            score=score,
            feedback=evaluation.get("feedback", ""),
            strengths=", ".join(evaluation.get("strengths", [])),
            improvements=", ".join(evaluation.get("improvements", [])),
        )

        # Adapt difficulty from the candidate's performance.
        new_difficulty = self._adjust_difficulty(
            score,
            interview.difficulty,
        )

        if new_difficulty != interview.difficulty:
            await self.repository.update_interview_difficulty(
                interview_id,
                new_difficulty,
            )

        # ---------------------------------------------------------
        # QUESTION LIMIT
        # ---------------------------------------------------------
        # Count questions that already received an answer.
        # The current answer has just been saved above.
        messages = await self.repository.get_messages(interview_id)

        answered_messages = [
            msg for msg in messages
            if msg.question and msg.answer is not None
        ]

        answered_count = len(answered_messages)
        max_questions = int(getattr(interview, "max_questions", 3) or 3)

        logger.info(
            "Interview progress: id=%s answered=%s max=%s",
            interview_id,
            answered_count,
            max_questions,
        )

        # Do NOT generate Q4, Q5, etc.
        if answered_count >= max_questions:
            await self.repository.update_interview_status(
                interview_id,
                InterviewStatus.COMPLETED,
            )

            evaluation["next_question"] = None
            evaluation["interview_complete"] = True
            evaluation["questions_answered"] = answered_count
            evaluation["max_questions"] = max_questions

            return format_evaluation_for_response(evaluation)

        # ---------------------------------------------------------
        # BUILD QUESTION MEMORY
        # ---------------------------------------------------------
        previous_questions = [
            msg.question.strip()
            for msg in messages
            if msg.question and msg.question.strip()
        ]

        # ---------------------------------------------------------
        # ROLE-AWARE TOPIC NORMALIZATION
        # ---------------------------------------------------------
        role = (interview.role or "").strip()
        topic = (interview.topic or "").strip()

        role_lower = role.lower()

        if (
            "frontend" in role_lower
            or "front-end" in role_lower
            or "react" in role_lower
            or "ui" in role_lower
        ):
            topic = "Frontend Development"

        elif (
            "backend" in role_lower
            or "back-end" in role_lower
            or "api" in role_lower
            or "server" in role_lower
        ):
            topic = "Backend Development"

        elif (
            "full stack" in role_lower
            or "full-stack" in role_lower
            or "fullstack" in role_lower
        ):
            topic = "Full Stack Development"

        elif (
            "data scientist" in role_lower
            or "data science" in role_lower
        ):
            topic = "Data Science"

        elif (
            "machine learning" in role_lower
            or "ml engineer" in role_lower
        ):
            topic = "Machine Learning"

        elif "devops" in role_lower or "cloud" in role_lower:
            topic = "DevOps and Cloud"

        elif (
            "python" in role_lower
            or "java" in role_lower
            or "software engineer" in role_lower
            or "software developer" in role_lower
        ):
            topic = "Software Engineering"

        elif (
            "dsa" in role_lower
            or "algorithm" in role_lower
            or "data structure" in role_lower
            or "dsa" in topic.lower()
        ):
            topic = "Data Structures and Algorithms"

        # ---------------------------------------------------------
        # QUESTION STAGE
        # ---------------------------------------------------------
        # Q1 = fundamentals
        # Q2 = deeper/practical
        # Q3 = advanced/edge-case
        question_number = answered_count + 1

        stage = {
            2: "Ask a deeper practical/application question. Do not repeat Q1.",
            3: "Ask an advanced scenario, trade-off, optimization, debugging, or edge-case question. Do not repeat earlier questions.",
        }.get(
            question_number,
            "Ask a progressively deeper technical question."
        )

        # ---------------------------------------------------------
        # GENERATE NEXT QUESTION
        # ---------------------------------------------------------
        try:
            next_question = await self.ai_provider.generate_question(
                topic=topic,
                difficulty=new_difficulty,
                previous_questions=previous_questions,
            )
        except Exception as exc:
            raise AIProviderException(
                message=f"Failed to generate next question: {str(exc)}"
            ) from exc

        next_question = (next_question or "").strip()

        # ---------------------------------------------------------
        # ANTI-REPETITION GUARD
        # ---------------------------------------------------------
        normalized_next = " ".join(next_question.lower().split())

        repeated = any(
            normalized_next == " ".join(q.lower().split())
            for q in previous_questions
        )

        if repeated or not next_question:
            fallback_questions = {
                "Frontend Development": [
                    "How does the browser render a modern frontend application from HTML, CSS, and JavaScript, and where can rendering performance become a bottleneck?",
                    "A React application becomes slow as the number of components grows. How would you diagnose the problem and decide between memoization, state restructuring, code splitting, and virtualization?",
                ],
                "Backend Development": [
                    "How would you design a REST API for a production backend, including validation, authentication, error handling, and HTTP status codes?",
                    "An API becomes slow under heavy traffic. How would you identify the bottleneck and improve database access, caching, concurrency, and scalability?",
                ],
                "Data Structures and Algorithms": [
                    "Given a sorted array, explain how Binary Search works, including its invariants, time complexity, and important edge cases.",
                    "How would you modify Binary Search to handle duplicate values and return the first occurrence while maintaining logarithmic time complexity?",
                ],
                "Software Engineering": [
                    "How would you design a maintainable software component with clear interfaces, validation, error handling, and testability?",
                    "A production service becomes slow as traffic increases. How would you systematically diagnose and optimize it?",
                ],
                "Data Science": [
                    "How would you handle missing values, outliers, categorical features, and data leakage when preparing a dataset for machine learning?",
                    "A model performs well on training data but poorly on unseen data. How would you diagnose overfitting and improve generalization?",
                ],
                "Machine Learning": [
                    "Explain the difference between training, validation, and test data and how you would use them to evaluate a machine learning model correctly.",
                    "A classifier has high accuracy but performs poorly on an important minority class. How would you diagnose and improve the model?",
                ],
                "DevOps and Cloud": [
                    "How would you design a CI/CD pipeline that safely builds, tests, deploys, and rolls back a production application?",
                    "A production service suddenly experiences high latency after deployment. How would you investigate the issue and perform a safe rollback or remediation?",
                ],
                "Full Stack Development": [
                    "Walk through the complete lifecycle of a request from a frontend application to a backend API, database, and response back to the browser.",
                    "A full-stack application works locally but becomes slow in production. How would you isolate whether the problem is frontend, network, backend, database, or infrastructure?",
                ],
            }

            candidates = fallback_questions.get(topic, [
                f"For a {role or 'software'} role, explain a practical technical problem you would solve using {topic}, including your design decisions, trade-offs, and edge cases.",
                f"For a {role or 'software'} role, describe how you would debug and optimize a production problem involving {topic}.",
            ])

            unused = [
                q for q in candidates
                if " ".join(q.lower().split()) not in {
                    " ".join(x.lower().split())
                    for x in previous_questions
                }
            ]

            if unused:
                next_question = unused[0]

        # ---------------------------------------------------------
        # SAVE ONLY ONE PENDING QUESTION
        # ---------------------------------------------------------
        await self.repository.save_message(
            interview_id=interview_id,
            question=next_question,
        )

        evaluation["next_question"] = next_question
        evaluation["interview_complete"] = False
        evaluation["questions_answered"] = answered_count
        evaluation["max_questions"] = max_questions
        evaluation["question_number"] = question_number
        evaluation["stage"] = stage

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


