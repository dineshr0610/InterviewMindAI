from __future__ import annotations

from ai_engine.services.rag_service import RAGService
from ai_engine.services.question_controller import AdaptiveQuestionController


class InterviewService:

    def __init__(self):
        self.rag = RAGService()

    def generate_question(
        self,
        topic,
        difficulty,
        previous_questions=None,
        focus=None,
    ):
        previous_questions = previous_questions or []

        controller = AdaptiveQuestionController(topic)

        if focus is None:
            focus = controller.choose_focus(
                difficulty,
                previous_questions
            )

        prompt = f"""
You are an expert technical interviewer.

HARD INTERVIEW TOPIC:
{topic}

CURRENT DIFFICULTY:
{difficulty}

TARGET CONCEPT:
{focus}

PREVIOUS QUESTIONS:
{previous_questions}

Generate exactly ONE interview question.

STRICT RULES:
1. The question MUST explicitly be about "{topic}".
2. Do NOT change the topic.
3. Do NOT generalize the topic.
4. Do NOT introduce an unrelated technology.
5. Do NOT repeat a previous question.
6. The question should test the TARGET CONCEPT.
7. Match the requested difficulty.
8. Return ONLY valid JSON.

Required format:

{{
    "answer": "one interview question"
}}
"""

        try:
            result = self.rag.ask(prompt)

            if isinstance(result, dict):
                question = (
                    result.get("answer")
                    or result.get("question")
                    or result.get("text")
                    or ""
                )
            else:
                question = str(result or "")

            valid, _ = controller.validate(
                question,
                previous_questions
            )

            if valid:
                return {"answer": question}

        except Exception:
            pass

        return {
            "answer": controller.fallback(
                difficulty,
                previous_questions
            )
        }
