"""
AI Provider facade for InterviewMind AI.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import asyncio
import logging
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

logger = logging.getLogger("interviewmind.providers.ai")

try:
    from ai_engine.services.interview_service import (
        InterviewService as AIInterviewService,
    )
    from ai_engine.services.evaluation_service import (
        EvaluationService as AIEvaluationService,
    )
    from ai_engine.graphs.interview_graph import interview_graph

    AI_ENGINE_AVAILABLE = True

except Exception as exc:
    logger.warning(
        "Could not import ai_engine: %s",
        exc,
    )
    AI_ENGINE_AVAILABLE = False


class AIProvider:

    def __init__(self) -> None:
        self.ai_service = (
            AIInterviewService()
            if AI_ENGINE_AVAILABLE
            else None
        )

        self.interview_graph = interview_graph if AI_ENGINE_AVAILABLE else None

        self.eval_service = (
            AIEvaluationService()
            if AI_ENGINE_AVAILABLE
            else None
        )

        logger.info(
            "AIProvider initialized (AI_ENGINE_AVAILABLE=%s)",
            AI_ENGINE_AVAILABLE,
        )

    async def generate_question(
        self,
        topic: str,
        difficulty: str = "Easy",
        previous_questions: Optional[list[str]] = None,
    ) -> str:

        previous_questions = previous_questions or []

        logger.info(
            "Generating topic-locked question: topic='%s', difficulty='%s'",
            topic,
            difficulty,
        )

        if self.interview_graph:
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.interview_graph.invoke,
                        {
                            "mode": "start",
                            "candidate_name": "",
                            "topic": topic,
                            "difficulty": difficulty,
                            "question": "",
                            "answer": "",
                            "score": 0,
                            "feedback": "",
                            "strengths": [],
                            "improvements": [],
                            "question_number": 0,
                            "max_questions": 1,
                            "interview_completed": False,
                            "history": [
                                {"question": question}
                                for question in previous_questions
                            ],
                        },
                    ),
                    timeout=30.0,
                )
                question = result.get("question") if isinstance(result, dict) else None
                if question:
                    return str(question).strip()
            except Exception as exc:
                logger.error("LangGraph question generation failed: %s", exc)

        if AI_ENGINE_AVAILABLE and self.ai_service:
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.ai_service.generate_question,
                        topic,
                        difficulty,
                        previous_questions,
                    ),
                    timeout=30.0,
                )

                if isinstance(result, dict):
                    question = (
                        result.get("answer")
                        or result.get("question")
                        or result.get("text")
                    )

                    if question:
                        return str(question).strip()

                if isinstance(result, str) and result.strip():
                    return result.strip()

            except Exception as exc:
                logger.error(
                    "Question generation failed: %s",
                    exc,
                )

        # Deterministic emergency fallback.
        from ai_engine.services.question_controller import (
            AdaptiveQuestionController,
        )

        controller = AdaptiveQuestionController(topic)

        return controller.fallback(
            difficulty,
            previous_questions,
        )

    async def process_answer(
        self,
        question: str,
        answer: str,
        topic: str,
        difficulty: str,
        history: list[dict],
        question_number: int,
        max_questions: int,
    ) -> Dict[str, Any]:
        """Execute the LangGraph answer turn and return its public result."""
        if self.interview_graph:
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.interview_graph.invoke,
                        {
                            "mode": "answer",
                            "candidate_name": "",
                            "topic": topic,
                            "difficulty": difficulty,
                            "question": question,
                            "answer": answer,
                            "score": 0,
                            "feedback": "",
                            "strengths": [],
                            "improvements": [],
                            "question_number": question_number,
                            "max_questions": max_questions,
                            "interview_completed": False,
                            "history": history,
                        },
                    ),
                    timeout=30.0,
                )
                if isinstance(result, dict) and "score" in result:
                    score = max(0, min(10, round(float(result.get("score", 0)))))
                    return {
                        "score": score,
                        "feedback": str(result.get("feedback", "")),
                        "strengths": result.get("strengths", []),
                        "improvements": result.get("improvements", []),
                        "next_question": None if result.get("interview_completed") else result.get("question"),
                        "difficulty": result.get("difficulty", difficulty),
                        "completed": bool(result.get("interview_completed")),
                    }
            except Exception as exc:
                logger.error("LangGraph answer processing failed: %s", exc)

        evaluation = await self.evaluate_answer(question, answer, topic, difficulty)
        return {**evaluation, "next_question": None, "difficulty": difficulty, "completed": False}

    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        topic: Optional[str] = None,
        difficulty: str = "Easy",
    ) -> Dict[str, Any]:

        logger.info(
            "Evaluating answer for topic='%s'",
            topic,
        )

        if AI_ENGINE_AVAILABLE and self.eval_service:

            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.eval_service.evaluate,
                        question,
                        answer,
                        topic,
                        difficulty,
                    ),
                    timeout=30.0,
                )

                if isinstance(result, dict) and "score" in result:

                    raw_score = float(result.get("score", 0))

                    # Support both 0-10 and 0-100 evaluator outputs.
                    if raw_score > 10:
                        score = round(raw_score / 10)
                    else:
                        score = round(raw_score)

                    score = max(0, min(10, score))

                    strengths = result.get(
                        "strengths",
                        ["Demonstrated subject knowledge"],
                    )

                    improvements = result.get(
                        "improvements",
                        ["Provide more concrete technical examples"],
                    )

                    if isinstance(strengths, str):
                        strengths = [
                            s.strip()
                            for s in strengths.split(",")
                            if s.strip()
                        ]

                    if isinstance(improvements, str):
                        improvements = [
                            s.strip()
                            for s in improvements.split(",")
                            if s.strip()
                        ]

                    return {
                        "score": score,
                        "feedback": str(
                            result.get(
                                "feedback",
                                "Good effort.",
                            )
                        ),
                        "strengths": strengths,
                        "improvements": improvements,
                    }

            except Exception as exc:
                logger.error(
                    "Answer evaluation failed: %s",
                    exc,
                )

        # Deterministic fallback evaluation.
        answer_len = len(answer.strip())

        if answer_len >= 250:
            score = 8
        elif answer_len >= 150:
            score = 7
        elif answer_len >= 80:
            score = 6
        elif answer_len >= 40:
            score = 5
        else:
            score = 3

        return {
            "score": score,
            "feedback": (
                "The answer demonstrates useful understanding. "
                "Add more technical detail, examples, and edge cases."
            ),
            "strengths": [
                "Attempted the question",
                "Communicated a technical explanation",
            ],
            "improvements": [
                "Add concrete implementation details",
                "Discuss complexity and edge cases",
            ],
        }

