from __future__ import annotations

from ai_engine.services.rag_service import RAGService
from ai_engine.services.question_controller import (
    AdaptiveQuestionController,
    DIVERSITY_PROMPTS,
    TOPIC_TRANSITION,
    choose_next_strategy,
)
from app.utils.resume import sanitize_resume_for_prompt


class InterviewService:

    def __init__(self):
        self.rag = RAGService()

    def generate_question(
        self,
        topic,
        difficulty,
        previous_questions=None,
        focus=None,
        resume_text=None,
        strategy=None,
        last_answer=None,
    ):
        previous_questions = previous_questions or []

        controller = AdaptiveQuestionController(topic)

        if focus is None:
            focus = controller.choose_focus(
                difficulty,
                previous_questions
            )

        resume_section = ""
        if resume_text:
            cleaned = sanitize_resume_for_prompt(resume_text)
            if cleaned:
                resume_section = f"""
CANDIDATE RESUME CONTEXT:
{cleaned}

When candidate resume context is provided, you MUST directly ground the question in the candidate's actual projects, claimed skills, or technical implementations from their resume (e.g. "In your resume, you built X using Y. How did you...").
The question must test genuine technical understanding of what the candidate actually built or used.
Do NOT invent skills, projects, or technologies that are not in the resume.
Return to the resume whenever it is relevant throughout the interview.
"""

        # Conversational section: decide what a real interviewer would ask next.
        conversational_section = ""
        if strategy:
            guidance = DIVERSITY_PROMPTS.get(strategy, "")
            is_transition = strategy == TOPIC_TRANSITION
            conversational_section = f"""
NEXT INTERVIEW ACTION:
{strategy}

ACTION GUIDANCE:
{guidance}

CANDIDATE'S MOST RECENT ANSWER (reference it directly when relevant):
{last_answer or "No previous answer yet."}

CONVERSATIONAL RULES:
1. First consider the candidate's most recent answer, then decide what a good
   interviewer would ask next.
2. Reference the candidate's own words or concepts (e.g. "You mentioned X...").
3. If the action is a follow-up / probe / clarification / edge case / tradeoff
   / scenario, build the question directly on the candidate's last answer.
4. If the action is a topic transition, acknowledge that one area is covered
   and move to another relevant aspect of the role/topic.
5. Vary your question templates. Do not repeatedly ask "Explain X." instead mix:
   "Explain X", "Why did you choose X?", "How did you implement X?", "What are
   the limitations of X?", "What happens if X fails?", "How would you optimize
   or scale X?", "Compare X and Y", "What trade-offs exist?", "Design a solution
   using X", "What would you change in production?".
6. Do not hardcode a strict script; use the strategy as guidance and stay
   natural and conversational.
"""

        prompt = f"""
You are an expert technical interviewer conducting a live, adaptive, realistic
interview. You behave like a real senior interviewer: you listen to the
candidate's answer, understand it, and decide what a good interviewer would
ask next.
{resume_section}
{conversational_section}
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
5. Do NOT repeat, or nearly repeat, a previous question.
6. The question should test the TARGET CONCEPT.
7. Match the requested difficulty.
8. If resume context is provided, personalize the question using it,
   testing understanding rather than confirming resume text.
9. Reference the candidate's last answer where the strategy calls for it.
10. Return ONLY valid JSON.

Required format:

{{
    "answer": "one interview question"
}}
"""

        # 1. When a resume is present: Generate directly from candidate resume content using Gemini AI
        if resume_text:
            try:
                from ai_engine.models.llm import llm
                if llm:
                    response = llm.invoke(prompt)
                    raw_text = getattr(response, "content", str(response)).strip()
                    import re
                    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group(0))
                        question = parsed.get("answer") or parsed.get("question") or ""
                    else:
                        question = raw_text

                    question = question.strip()
                    if question and len(question) > 15 and not any(
                        question.lower() == p.lower() for p in previous_questions
                    ):
                        return {"answer": question}
            except Exception:
                pass

            # Smart resume-grounded fallback if API is unreachable
            return {
                "answer": (
                    f"In your resume, you highlight experience with {topic}. "
                    f"Could you walk me through a specific project where you implemented {topic}, "
                    f"and explain the key technical trade-offs or performance challenges you encountered?"
                )
            }

        # 2. When no resume (or core technical phase): Retrieve from Supabase Question Bank via RAG
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
