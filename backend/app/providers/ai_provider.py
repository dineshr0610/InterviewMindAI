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
        resume_text: Optional[str] = None,
        strategy: Optional[str] = None,
        last_answer: Optional[str] = None,
        role: Optional[str] = None,
        resume_match: Optional[dict] = None,
        interview_phase: Optional[str] = None,
        state: Optional[dict] = None,
        return_metadata: bool = False,
    ) -> Any:

        previous_questions = previous_questions or []

        logger.info(
            "Generating question: topic='%s', difficulty='%s', role='%s', phase='%s'",
            topic,
            difficulty,
            role,
            interview_phase,
        )

        if self.interview_graph and not resume_match:
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
                            "max_questions": 0,
                            "interview_completed": False,
                            "history": [
                                {"question": question}
                                for question in previous_questions
                            ],
                            "resume_text": resume_text,
                            "next_strategy": strategy or "",
                            "follow_up_depth": 0,
                        },
                    ),
                    timeout=30.0,
                )
                question = result.get("question") if isinstance(result, dict) else None
                if question:
                    return result if return_metadata and isinstance(result, dict) else str(question).strip()
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
                        resume_text=resume_text,
                        strategy=strategy,
                        last_answer=last_answer,
                        role=role,
                        resume_match=resume_match,
                        interview_phase=interview_phase,
                        state=state,
                    ),
                    timeout=30.0,
                )

                if isinstance(result, dict):
                    if return_metadata:
                        return result
                    question = (
                        result.get("answer")
                        or result.get("question")
                        or result.get("text")
                    )

                    if question:
                        return str(question).strip()

                if isinstance(result, str) and result.strip():
                    return {"answer": result.strip()} if return_metadata else result.strip()

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
        fallback_text = controller.fallback(
            difficulty,
            previous_questions,
        )
        if return_metadata:
            return {
                "answer": fallback_text,
                "source": "fallback",
                "category": "implementation",
                "intent": "implement",
                "difficulty": difficulty,
            }
        return fallback_text

    async def process_answer(
        self,
        question: str,
        answer: str,
        topic: str,
        difficulty: str,
        history: list[dict],
        question_number: int,
        max_questions: int,
        resume_text: Optional[str] = None,
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
                            "resume_text": resume_text,
                            "next_strategy": "",
                            "follow_up_depth": 0,
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
        return {**evaluation, "next_question": None, "difficulty": None, "completed": False}

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

        # Deterministic fallback evaluation (evidence-aware heuristic).
        import re

        stop_words = {
            "what", "how", "why", "explain", "describe", "compare", "the", "and", "is",
            "in", "to", "of", "a", "an", "with", "for", "on", "are", "you", "would",
            "could", "should", "it", "this", "that", "can", "be", "as", "by", "or",
            "not", "have", "has", "had", "do", "does", "did", "from", "at", "but",
            "about", "which", "when", "where", "who", "whom", "whose", "we", "they",
            "them", "then", "there", "their", "so", "if", "your", "my", "our", "us",
            "will", "shall", "may", "might", "must", "benefits", "trade", "offs",
            "pros", "cons", "advantages", "disadvantages", "differences", "between",
            "using", "use", "used", "uses", "tell", "me", "about", "give", "example",
            "examples", "some", "any", "all", "more", "less", "most", "least", "very"
        }

        def tokenize(text: str) -> set:
            words = set()
            for word in re.findall(r"\b[a-zA-Z0-9]+\b", text or ""):
                lower_word = word.lower()
                if len(lower_word) > 2 and lower_word not in stop_words:
                    words.add(lower_word)
            return words

        q_tokens = tokenize(question)
        topic_tokens = tokenize(topic) if topic else set()
        target_tokens = q_tokens.union(topic_tokens)

        if not target_tokens:
            target_tokens = {"data", "system", "code", "application"}

        a_tokens = tokenize(answer)

        matched_tokens = set()
        for at in a_tokens:
            for tt in target_tokens:
                # Exact match or prefix match for words 4+ chars
                if at == tt or (len(tt) >= 4 and len(at) >= 4 and at[:4] == tt[:4]):
                    matched_tokens.add(tt)

        tech_vocab_count = len([w for w in a_tokens if len(w) > 4])
        coverage_ratio = len(matched_tokens) / max(1, len(target_tokens))

        score = 2.0  # Base score for attempting with non-empty answer

        if coverage_ratio >= 0.5:
            score += 4.0
        elif coverage_ratio >= 0.3:
            score += 3.0
        elif coverage_ratio > 0.0:
            score += 1.0

        if tech_vocab_count >= 15 and coverage_ratio >= 0.2:
            score += 2.0
        elif tech_vocab_count >= 8 and coverage_ratio >= 0.1:
            score += 1.0
        elif tech_vocab_count >= 3 and coverage_ratio == 0.0:
            # Minor points for using technical words even if missed exact concepts
            score += 1.0

        if not a_tokens:
            score = 0.0
        elif len(answer.strip()) > 150 and coverage_ratio == 0.0:
            # Penalize long irrelevant answers
            score = 1.0

        score = max(0, min(10, round(score)))

        return {
            "score": score,
            "feedback": (
                "The answer has been evaluated using a fallback heuristic. "
                "Ensure your answers directly address the technical concepts "
                "mentioned in the question."
            ),
            "strengths": [
                "Attempted the question"
            ] if score > 0 else [],
            "improvements": [
                "Add concrete implementation details",
                "Ensure direct relevance to the question's core concepts",
            ],
        }


