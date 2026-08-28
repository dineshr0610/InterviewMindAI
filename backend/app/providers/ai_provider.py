"""
AI Provider facade for InterviewMind AI.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import asyncio
import logging
import sys
import time
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
            "[start] Generating question: topic='%s', difficulty='%s'",
            topic,
            difficulty,
        )

        # Try LangGraph first (includes RAG + validation)
        if self.interview_graph:
            start_time = time.time()
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
                    timeout=15.0,  # Reduced from 30s for faster fallback
                )
                question = result.get("question") if isinstance(result, dict) else None
                if question:
                    elapsed_ms = (time.time() - start_time) * 1000
                    logger.info("[start] question_generation_ms=%.0f", elapsed_ms)
                    return str(question).strip()
            except Exception as exc:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.warning("[start] LangGraph failed after %.0fms: %s", elapsed_ms, exc)

        # Skip the nested retry loop. Go directly to deterministic fallback.
        # This prevents the dual retry (LangGraph timeout -> InterviewService retry -> another timeout).
        logger.info("[start] Using deterministic fallback (no nested AI calls)")
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
            start_time = time.time()
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
                    timeout=15.0,  # Reduced from 30s for faster fallback
                )
                if isinstance(result, dict) and "score" in result:
                    score = max(0, min(10, round(float(result.get("score", 0)))))
                    elapsed_ms = (time.time() - start_time) * 1000
                    logger.info("[answer] evaluation_ms=%.0f", elapsed_ms)
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
                elapsed_ms = (time.time() - start_time) * 1000
                logger.warning("[answer] LangGraph failed after %.0fms, using fallback: %s", elapsed_ms, exc)

        # Use deterministic fallback instead of calling evaluate_answer (which would retry LLM).
        # This avoids the dual timeout: LangGraph timeout (15s) -> evaluate_answer timeout (30s) = 45s wait.
        logger.info("[answer] Using deterministic fallback (no nested LLM calls)")
        return self._deterministic_evaluation(question, answer, topic, difficulty, history, question_number, max_questions)

    def _deterministic_evaluation(
        self,
        question: str,
        answer: str,
        topic: str,
        difficulty: str,
        history: list[dict],
        question_number: int,
        max_questions: int,
    ) -> Dict[str, Any]:
        """
        Deterministic fallback evaluation and next question generation.
        Used when LangGraph or LLM calls fail to avoid long retry waits.
        """
        # Length-based score (deterministic, no AI)
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

        # Deterministic feedback
        feedback = "Good effort. "
        if score >= 8:
            feedback += "Your answer demonstrates strong technical understanding."
        elif score >= 6:
            feedback += "Your answer shows solid understanding. Add more detail for stronger responses."
        else:
            feedback += "Your answer is a good start. Provide more comprehensive technical details."

        # Strengths and improvements (deterministic)
        strengths = ["Provided a response"]
        if answer_len >= 80:
            strengths.append("Good depth of explanation")
        if "example" in answer.lower():
            strengths.append("Included concrete examples")
        
        improvements = ["Elaborate further on implementation details"]
        if score < 7:
            improvements.append("Add more technical depth")
        if "complexity" not in answer.lower():
            improvements.append("Discuss time/space complexity")

        # Deterministic next question (from controller fallback)
        from ai_engine.services.question_controller import AdaptiveQuestionController
        controller = AdaptiveQuestionController(topic)
        
        previous_questions = [h.get("question", "") for h in history]
        next_question = None
        
        # Only generate next question if not at max
        if question_number + 1 < max_questions:
            next_question = controller.fallback(difficulty, previous_questions)

        # Difficulty stays the same in fallback (service layer will adjust it based on score)
        return {
            "score": score,
            "feedback": feedback,
            "strengths": strengths,
            "improvements": improvements,
            "next_question": next_question,
            "difficulty": None,  # Let service layer adjust
            "completed": question_number + 1 >= max_questions,
        }

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

