"""
AI Provider — Facade interface for Gunal's LangGraph AI engine.
The backend calls this provider to generate questions and evaluate candidate answers.
It abstracts all LLM/LangChain/LangGraph execution details away from the application logic.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure backend directory is in sys.path so ai_engine can be imported
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

logger = logging.getLogger("interviewmind.providers.ai")

try:
    from ai_engine.services.interview_service import InterviewService as AIInterviewService
    from ai_engine.services.evaluation_service import EvaluationService as AIEvaluationService
    from ai_engine.graphs.interview_graph import interview_graph
    AI_ENGINE_AVAILABLE = True
    logger.info("Successfully imported ai_engine modules.")
except Exception as exc:
    logger.warning("Could not import ai_engine directly: %s. Using fallback provider logic.", exc)
    AI_ENGINE_AVAILABLE = False


class AIProvider:
    """
    Facade Provider interfacing with Gunal's LangGraph engine.
    Exposes strictly generate_question() and evaluate_answer().
    """

    def __init__(self) -> None:
        """Initialize the AI provider facade."""
        self.ai_service = AIInterviewService() if AI_ENGINE_AVAILABLE else None
        self.eval_service = AIEvaluationService() if AI_ENGINE_AVAILABLE else None
        logger.info("AIProvider facade initialized (AI_ENGINE_AVAILABLE=%s).", AI_ENGINE_AVAILABLE)

    async def generate_question(
        self,
        topic: str,
        difficulty: str = "Easy",
    ) -> str:
        """
        Generate an interview question for the given topic and difficulty.

        Args:
            topic: The technical topic for the question.
            difficulty: Difficulty level ("Easy", "Medium", "Hard").

        Returns:
            A generated interview question text.
        """
        logger.info(
            "Generating question via AIProvider: topic='%s', difficulty='%s'",
            topic,
            difficulty,
        )

        if AI_ENGINE_AVAILABLE and self.ai_service:
            try:
                res = await asyncio.wait_for(
                    asyncio.to_thread(self.ai_service.generate_question, topic, difficulty),
                    timeout=3.0,
                )
                if isinstance(res, dict):
                    q = res.get("question") or res.get("answer") or res.get("text")
                    if q:
                        return str(q)
                elif isinstance(res, str) and res.strip():
                    return res.strip()
            except Exception as exc:
                logger.error("Error or timeout invoking ai_engine for question generation: %s", exc)

        # Fallback question generator
        questions = {
            "Easy": f"Can you explain the fundamental principles and core concepts of {topic}?",
            "Medium": f"Describe how you would design and implement a scalable solution using {topic}.",
            "Hard": f"Design a production-grade architecture using {topic}, covering performance bottlenecks, security, and edge cases.",
        }

        return questions.get(difficulty, questions["Easy"])

    async def evaluate_answer(
        self,
        question: str,
        answer: str,
    ) -> Dict[str, Any]:
        """
        Evaluate a candidate's answer using Gunal's evaluation engine.

        Args:
            question: The interview question asked.
            answer: The candidate's response text.

        Returns:
            A dictionary containing score, feedback, strengths, improvements, next_question.
        """
        logger.info(
            "Evaluating answer via AIProvider for question: '%s...'",
            question[:50] if len(question) > 50 else question,
        )

        if AI_ENGINE_AVAILABLE and self.eval_service:
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(self.eval_service.evaluate, question, answer),
                    timeout=3.0,
                )
                if isinstance(result, dict) and "score" in result:
                    next_q = await self.generate_question(
                        topic=topic_from_question(question),
                        difficulty="Medium" if result.get("score", 0) >= 8 else "Easy"
                    )
                    strengths = result.get("strengths", ["Demonstrated subject knowledge"])
                    if isinstance(strengths, str):
                        strengths = [s.strip() for s in strengths.split(",") if s.strip()]
                    
                    improvements = result.get("improvements", ["Provide more concrete examples"])
                    if isinstance(improvements, str):
                        improvements = [i.strip() for i in improvements.split(",") if i.strip()]

                    return {
                        "score": int(result.get("score", 5)),
                        "feedback": str(result.get("feedback", "Good effort.")),
                        "strengths": strengths,
                        "improvements": improvements,
                        "next_question": next_q,
                    }
            except Exception as exc:
                logger.error("Error or timeout invoking ai_engine for answer evaluation: %s", exc)

        # Fallback evaluation logic
        answer_len = len(answer.strip())
        score = min(10, max(1, answer_len // 40))
        topic = topic_from_question(question)
        next_q = await self.generate_question(topic=topic, difficulty="Medium" if score >= 8 else "Easy")

        return {
            "score": score,
            "feedback": (
                "The response shows solid foundational understanding. "
                "Consider adding more concrete code examples and technical depth."
                if score >= 6
                else "The response addresses the question at a basic level. "
                     "Expand further on technical mechanisms and architectural trade-offs."
            ),
            "strengths": [
                "Clear communication structure",
                "Addressed the primary question directly",
            ] if score >= 6 else [
                "Attempted the question",
            ],
            "improvements": [
                "Provide specific technical examples",
                "Discuss edge cases and performance implications",
            ],
            "next_question": next_q,
        }


def topic_from_question(question: str) -> str:
    """Helper to extract topic keyword from question string."""
    words = question.split()
    return words[-1].strip("?.") if words else "this topic"
