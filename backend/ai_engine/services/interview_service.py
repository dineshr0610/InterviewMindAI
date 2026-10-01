from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from ai_engine.services.rag_service import RAGService
from ai_engine.services.question_controller import (
    AdaptiveQuestionController,
    ALL_QUESTION_CATEGORIES,
    ALL_QUESTION_INTENTS,
    CAT_API,
    CAT_ARCHITECTURE,
    CAT_DATABASE,
    CAT_DATA_FLOW,
    CAT_DEBUGGING,
    CAT_FOLLOW_UP,
    CAT_IMPLEMENTATION,
    CAT_MISSING_SKILL,
    CAT_PERFORMANCE,
    CAT_ROLE_COMPETENCY,
    CAT_SECURITY,
    CAT_TECH_CHOICE,
    CAT_TRADEOFFS,
    INTENT_ARCHITECTURE,
    INTENT_COMPARE,
    INTENT_DEBUG,
    INTENT_DESIGN,
    INTENT_EXPERIENCE,
    INTENT_EXPLAIN,
    INTENT_FUNDAMENTALS,
    INTENT_IMPLEMENT,
    INTENT_JUSTIFY,
    INTENT_OPTIMIZE,
    INTENT_PREDICT,
    INTENT_REASONING,
    INTENT_SCENARIO,
    INTENT_TRADEOFF,
    detect_question_intent,
    choose_next_strategy,
)
from app.utils.resume import sanitize_resume_for_prompt

logger = logging.getLogger("interviewmind.ai_engine.interview_service")

# Standard Question Source Identifiers
SOURCE_GEMINI_RESUME = "gemini_resume"
SOURCE_SUPABASE_BANK = "supabase_bank"
SOURCE_FOLLOW_UP = "follow_up"
SOURCE_MISSING_SKILL = "missing_skill"
SOURCE_ROLE_BANK = "role_bank"


def extract_llm_text(response: Any) -> str:
    """Extract clean string text from LLM response across LangChain, Google GenAI, and fallback objects."""
    if response is None:
        return ""
    if isinstance(response, str):
        return response.strip()
    if hasattr(response, "text") and isinstance(response.text, str) and response.text.strip():
        return response.text.strip()
    content = getattr(response, "content", None)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(str(part["text"]))
            elif hasattr(part, "text"):
                parts.append(str(part.text))
        if parts:
            return "".join(parts).strip()
    return str(response).strip()


@dataclass
class QuestionCandidate:
    text: str
    source: str
    category: str
    topic: str
    intent: str
    project: Optional[str] = None
    technology: Optional[str] = None
    difficulty: str = "Medium"
    
    # Evaluation Scores (0.0 to 10.0 scale)
    role_relevance: float = 0.0
    resume_relevance: float = 0.0
    interview_value: float = 0.0
    novelty: float = 0.0
    difficulty_fit: float = 0.0
    answer_continuation_value: float = 0.0
    coverage_value: float = 0.0
    
    # Penalties
    hallucination_penalty: float = 0.0
    repetition_penalty: float = 0.0
    generic_penalty: float = 0.0
    
    score: float = 0.0
    is_valid: bool = True
    rejection_reason: Optional[str] = None
    selection_reason: Optional[str] = None


class QuestionQualityEvaluator:
    """Evaluates question candidates for quality, role relevance, grounding, novelty, and validity."""

    ROLE_PRIORITY_CATEGORIES = {
        "frontend": [CAT_ARCHITECTURE, CAT_DATA_FLOW, CAT_IMPLEMENTATION, CAT_TECH_CHOICE, CAT_SECURITY, CAT_DEBUGGING, CAT_PERFORMANCE, CAT_TRADEOFFS, CAT_ROLE_COMPETENCY],
        "backend": [CAT_ARCHITECTURE, CAT_DATA_FLOW, CAT_IMPLEMENTATION, CAT_DATABASE, CAT_API, CAT_SECURITY, CAT_DEBUGGING, CAT_PERFORMANCE, CAT_TRADEOFFS, CAT_ROLE_COMPETENCY],
        "data": [CAT_DATABASE, CAT_IMPLEMENTATION, CAT_DATA_FLOW, CAT_DEBUGGING, CAT_TRADEOFFS, CAT_ROLE_COMPETENCY],
        "machine_learning": [CAT_ARCHITECTURE, CAT_DATA_FLOW, CAT_IMPLEMENTATION, CAT_TECH_CHOICE, CAT_PERFORMANCE, CAT_TRADEOFFS, CAT_ROLE_COMPETENCY],
        "ai": [CAT_ARCHITECTURE, CAT_DATA_FLOW, CAT_IMPLEMENTATION, CAT_TECH_CHOICE, CAT_PERFORMANCE, CAT_TRADEOFFS, CAT_ROLE_COMPETENCY],
    }

    GENERIC_QUESTION_PATTERNS = [
        "what is full stack development",
        "what is frontend development",
        "what is backend development",
        "what is software engineering",
        "how does it reduce the search space",
        "what is polymorphism",
        "what is an object",
    ]

    @classmethod
    def evaluate(
        cls,
        candidate: QuestionCandidate,
        *,
        role_name: str,
        verified_technologies: List[str],
        verified_projects: List[str],
        unsupported_technologies: List[str],
        missing_skills: List[str],
        previous_questions: List[str],
        recent_intents: List[str],
        categories_covered: List[str],
        projects_covered: List[str],
        technologies_covered: List[str],
        last_answer: Optional[str] = None,
        strategy: Optional[str] = None,
        target_difficulty: str = "Medium",
    ) -> QuestionCandidate:
        text = candidate.text.strip()
        q_lower = text.lower()

        # 1. Base length, syntax & vagueness check
        words = re.findall(r"\b[a-z0-9]+\b", q_lower)
        vague_phrases = [
            "tell me about it",
            "what about it",
            "how about it",
            "explain it",
            "tell me more",
            "can you explain it",
            "tell us about it",
        ]
        is_imperative_prompt = q_lower.startswith((
            "explain", "describe", "walk me through", "compare", "discuss",
            "outline", "detail", "clarify", "elaborate"
        ))
        if len(text) < 15 or ("?" not in text and not is_imperative_prompt):
            candidate.is_valid = False
            candidate.rejection_reason = "Question text too short or not a valid question / prompt"
            return candidate

        if len(words) < 5 or any(vp in q_lower for vp in vague_phrases):
            candidate.is_valid = False
            candidate.rejection_reason = "Technically vague question lacking substantive technical context"
            return candidate

        # 2. Exact or near-duplicate check
        for prev in previous_questions:
            p_lower = prev.lower().strip()
            if q_lower == p_lower:
                candidate.is_valid = False
                candidate.rejection_reason = "Exact duplicate of previously asked question"
                return candidate
            
            q_words = set(re.findall(r"\b[a-z0-9]+\b", q_lower))
            p_words = set(re.findall(r"\b[a-z0-9]+\b", p_lower))
            if q_words and p_words:
                sim = len(q_words & p_words) / max(1, len(q_words | p_words))
                if sim >= 0.70:
                    candidate.is_valid = False
                    candidate.rejection_reason = f"Near duplicate of previous question (similarity: {sim:.2f})"
                    return candidate

        # 3. Semantic repetition check: (same project/technology + same intent)
        if candidate.project or candidate.technology:
            subj = (candidate.project or candidate.technology or "").lower()
            for prev_q in previous_questions:
                prev_lower = prev_q.lower()
                if (subj in q_lower and subj in prev_lower) or any(
                    tok in q_lower and tok in prev_lower for tok in subj.split() if len(tok) > 3
                ):
                    prev_intent = detect_question_intent(prev_q)
                    if candidate.intent == prev_intent and candidate.intent in (
                        INTENT_ARCHITECTURE,
                        INTENT_DESIGN,
                        INTENT_JUSTIFY,
                        INTENT_TRADEOFF,
                        INTENT_DEBUG,
                    ):
                        candidate.is_valid = False
                        candidate.rejection_reason = f"Semantic duplicate: same subject ({subj}) and intent ({candidate.intent})"
                        return candidate

        # 4. Hallucination check: False claims of experience with unverified tools
        if candidate.source == SOURCE_GEMINI_RESUME and unsupported_technologies:
            for unsupp in unsupported_technologies:
                u_term = unsupp.lower().strip()
                if u_term and u_term in q_lower:
                    factual_phrases = [
                        f"you implemented {u_term}",
                        f"you built {u_term}",
                        f"you used {u_term}",
                        f"in your {u_term}",
                        f"your {u_term} project",
                        f"your experience with {u_term}",
                        f"highlight experience with {u_term}",
                    ]
                    factual_regex = rf"\b(?:you (?:implemented|built|used|deployed|designed)(?:\s+(?:a|an|the))?\s+{re.escape(u_term)}|in your\s+(?:project\s+)?{re.escape(u_term)}|your\s+{re.escape(u_term)}\s+project|your experience with\s+{re.escape(u_term)})"
                    has_factual_claim = any(fp in q_lower for fp in factual_phrases) or bool(re.search(factual_regex, q_lower))
                    is_hypothetical = any(
                        hyp in q_lower
                        for hyp in [
                            "if you needed",
                            "how would you",
                            "hypothetical",
                            "suppose",
                            "does not mention",
                            "would you evaluate",
                            "if traffic increased",
                        ]
                    )
                    if has_factual_claim and not is_hypothetical:
                        candidate.is_valid = False
                        candidate.rejection_reason = f"Unsupported claim: asserts candidate built/used unverified {unsupp}"
                        return candidate

        # 5. Generic question penalty
        if any(pat in q_lower for pat in cls.GENERIC_QUESTION_PATTERNS):
            candidate.generic_penalty = 8.0
            if verified_technologies or verified_projects:
                candidate.is_valid = False
                candidate.rejection_reason = "Generic textbook trivia rejected because verified resume evidence exists"
                return candidate

        # -------------------------------------------------------------
        # DIMENSIONAL SCORING
        # -------------------------------------------------------------
        # A. Role Relevance (0 to 10)
        role_lower = role_name.lower()
        role_cats = cls.ROLE_PRIORITY_CATEGORIES.get("backend", ALL_QUESTION_CATEGORIES)
        for rk, cats in cls.ROLE_PRIORITY_CATEGORIES.items():
            if rk in role_lower:
                role_cats = cats
                break
        
        if candidate.category == CAT_FOLLOW_UP or candidate.source == SOURCE_FOLLOW_UP:
            candidate.role_relevance = 9.5
        elif candidate.category in role_cats:
            cat_rank = role_cats.index(candidate.category)
            candidate.role_relevance = max(6.0, 10.0 - (cat_rank * 0.4))
        else:
            candidate.role_relevance = 5.0

        # Tech-role alignment bonus
        if "backend" in role_lower and any(t in q_lower for t in ["postgres", "sql", "api", "node", "database", "query", "index", "concurrency", "csrf", "token", "auth"]):
            candidate.role_relevance = min(10.0, candidate.role_relevance + 1.5)
        elif "frontend" in role_lower and any(t in q_lower for t in ["react", "component", "state", "dom", "rendering", "css", "browser", "hook"]):
            candidate.role_relevance = min(10.0, candidate.role_relevance + 1.5)

        # B. Resume Relevance & Grounding (0 to 10)
        if candidate.source == SOURCE_FOLLOW_UP:
            candidate.resume_relevance = 9.8 if last_answer else 9.0
        elif candidate.source == SOURCE_GEMINI_RESUME:
            candidate.resume_relevance = 9.5
        elif candidate.source == SOURCE_MISSING_SKILL:
            candidate.resume_relevance = 7.5
        else:
            candidate.resume_relevance = 6.5

        # C. Answer Continuation Value (0 to 10)
        if candidate.source == SOURCE_FOLLOW_UP and last_answer:
            ans_len = len(last_answer.strip())
            if ans_len >= 80:
                candidate.answer_continuation_value = 9.5
            elif ans_len >= 40:
                candidate.answer_continuation_value = 8.0
            else:
                candidate.answer_continuation_value = 6.0
            # Boost follow-up when adaptive strategy explicitly requests deepening
            if strategy in ("follow_up", "deeper_probe", "edge_case", "tradeoff"):
                candidate.answer_continuation_value = min(10.0, candidate.answer_continuation_value + 3.0)
        elif strategy in ("follow_up", "deeper_probe", "edge_case", "tradeoff"):
            candidate.answer_continuation_value = 7.0
        else:
            candidate.answer_continuation_value = 4.0

        # D. Novelty (0 to 10)
        if candidate.intent not in recent_intents[-3:]:
            candidate.novelty = 9.0
        elif candidate.intent not in recent_intents[-1:]:
            candidate.novelty = 7.0
        else:
            candidate.novelty = 5.0

        # E. Difficulty Fit (0 to 10)
        candidate.difficulty_fit = 8.5

        # F. Coverage Value (0 to 4) - Secondary tie-breaker
        cov = 0.0
        if candidate.project and candidate.project not in projects_covered:
            cov += 1.5
        if candidate.technology and candidate.technology not in technologies_covered:
            cov += 1.5
        if candidate.category and candidate.category not in categories_covered:
            cov += 1.0
        candidate.coverage_value = min(4.0, cov)

        # G. Interview Value Base (reduced from 8.0 to 5.0 for wider score differentiation)
        candidate.interview_value = 5.0

        # Calculate Total Score
        candidate.score = round(
            candidate.role_relevance
            + candidate.resume_relevance
            + candidate.interview_value
            + candidate.novelty
            + candidate.difficulty_fit
            + candidate.answer_continuation_value
            + candidate.coverage_value
            - candidate.hallucination_penalty
            - candidate.repetition_penalty
            - candidate.generic_penalty,
            2
        )
        return candidate


class InterviewService:

    def __init__(self):
        self.rag = RAGService()

    def generate_question(
        self,
        topic: str,
        difficulty: str = "Easy",
        previous_questions: list[str] | None = None,
        focus: str | None = None,
        resume_text: str | None = None,
        strategy: str | None = None,
        last_answer: str | None = None,
        role: str | None = None,
        resume_match: dict | None = None,
        interview_phase: str | None = None,
        state: dict | None = None,
    ) -> dict:
        previous_questions = previous_questions or []
        state_dict = state or {}

        # ------------------------------------------------------------------
        # 1. Extract Structured Resume Inventory & State Knowledge
        # ------------------------------------------------------------------
        match_data = resume_match or {}
        role_name = (
            role
            or match_data.get("role")
            or match_data.get("role_name")
            or "Software Engineer"
        )
        matched_skills = match_data.get("matched_skills") or match_data.get("matching_skills") or []
        matched_technologies = match_data.get("matched_technologies") or match_data.get("relevant_technologies") or []
        matched_projects = match_data.get("matched_projects") or match_data.get("relevant_projects") or []
        matched_experience = match_data.get("matched_experience") or match_data.get("relevant_experience") or []
        missing_skills = match_data.get("missing_skills") or []
        evidence_list = match_data.get("evidence") or []

        topic_inventory = match_data.get("topic_inventory") or state_dict.get("topic_inventory") or {}
        projects_inventory = topic_inventory.get("projects") or [
            {"name": str(p).split("\n")[0].strip(), "evidence": str(p), "technologies": matched_technologies[:3]}
            for p in matched_projects
        ]
        technologies_inventory = topic_inventory.get("technologies") or matched_technologies or matched_skills
        
        projects_covered = list(state_dict.get("projects_covered") or [])
        technologies_covered = list(state_dict.get("technologies_covered") or [])
        categories_covered = list(state_dict.get("categories_covered") or [])
        missing_skills_covered = list(state_dict.get("missing_skills_covered") or [])
        recent_intents = list(state_dict.get("recent_question_intents") or [])

        # List of technologies unsupported by the candidate's resume
        unsupported_technologies = [
            s for s in missing_skills
            if s.lower() not in " ".join(technologies_inventory).lower()
        ]

        has_resume = bool(resume_text or matched_skills or matched_projects)
        turn_count = len(previous_questions)

        # ------------------------------------------------------------------
        # 2. Determine Focus Project, Technology, and Category
        # ------------------------------------------------------------------
        unexplored_projects = [
            p for p in projects_inventory
            if (p.get("name") if isinstance(p, dict) else str(p)) not in projects_covered
        ]
        target_proj_dict = unexplored_projects[0] if unexplored_projects else (projects_inventory[0] if projects_inventory else None)
        target_proj_name = (target_proj_dict.get("name") if isinstance(target_proj_dict, dict) else str(target_proj_dict)) if target_proj_dict else ""
        target_proj_evidence = (target_proj_dict.get("evidence") if isinstance(target_proj_dict, dict) else str(target_proj_dict)) if target_proj_dict else ""

        unexplored_techs = [t for t in technologies_inventory if t not in technologies_covered]
        target_technology = unexplored_techs[0] if unexplored_techs else (technologies_inventory[0] if technologies_inventory else topic)

        # Dynamic category selection based on role priorities
        role_cats = QuestionQualityEvaluator.ROLE_PRIORITY_CATEGORIES.get("backend", ALL_QUESTION_CATEGORIES)
        for rk, cats in QuestionQualityEvaluator.ROLE_PRIORITY_CATEGORIES.items():
            if rk in role_name.lower():
                role_cats = cats
                break

        uncovered_cats = [c for c in role_cats if c not in categories_covered[-4:]]
        target_category = uncovered_cats[0] if uncovered_cats else role_cats[turn_count % len(role_cats)]

        controller = AdaptiveQuestionController(topic)
        candidate_pool: List[QuestionCandidate] = []

        # ------------------------------------------------------------------
        # 3. GENERATE CANDIDATE POOL (Multi-Source Generation)
        # ------------------------------------------------------------------

        # --- Candidate A: Conversational Follow-Up (if candidate provided substantive answer) ---
        if last_answer and len(last_answer.strip()) >= 20 and strategy in ("follow_up", "clarification", "deeper_probe", "edge_case", "tradeoff", "scenario", "architecture"):
            follow_up_prompt = f"""
You are a senior technical interviewer for {role_name}.
The candidate just answered your previous technical question.

TARGET ROLE: {role_name}
CANDIDATE'S LAST ANSWER:
"{last_answer}"

INTERVIEW GOAL:
Ask a sharp, concrete technical follow-up question directly investigating what the candidate claimed in their answer.
Probe into:
- Technical trade-offs or limitations of the approach they described
- Edge cases, error handling, or concurrency/failure scenarios
- Concrete mechanics or implementation details

STRICT RULES:
1. Ground the follow-up directly in what the candidate explicitly stated.
2. DO NOT ask generic textbook questions (e.g. "What is Full Stack Development?").
3. DO NOT repeat previous questions.
4. Return ONLY valid JSON:
{{
    "question": "Your single conversational follow-up question here"
}}
"""
            try:
                from ai_engine.models.llm import llm
                if llm:
                    response = llm.invoke(follow_up_prompt)
                    raw_text = extract_llm_text(response)
                    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group(0))
                        q_text = parsed.get("question") or parsed.get("answer") or ""
                    else:
                        q_text = raw_text
                    q_text = q_text.strip().strip('"').strip("'")
                    if q_text and len(q_text) >= 15:
                        intent = detect_question_intent(q_text)
                        candidate_pool.append(QuestionCandidate(
                            text=q_text,
                            source=SOURCE_FOLLOW_UP,
                            category=CAT_FOLLOW_UP,
                            topic=topic,
                            intent=intent,
                            project=target_proj_name,
                            technology=target_technology,
                            difficulty=difficulty,
                            selection_reason="Candidate provided substantive technical claims; probing trade-offs and edge cases."
                        ))
            except Exception as exc:
                logger.warning("Follow-up generation error: %s", exc)

        # --- Candidate B: Gemini Resume-Grounded Question ---
        if has_resume and interview_phase == "resume_phase":
            cleaned_resume = sanitize_resume_for_prompt(resume_text or "")
            evidence_block = target_proj_evidence or (
                "\n".join(f"- {e}" for e in evidence_list[:6]) if evidence_list else cleaned_resume[:1500]
            )

            category_instructions = {
                CAT_ARCHITECTURE: f"Ask about the high-level system architecture, component boundaries, and design patterns used in {target_proj_name or target_technology}.",
                CAT_DATA_FLOW: f"Ask how data flows end-to-end through {target_proj_name or target_technology}, from client request to backend/database and back.",
                CAT_IMPLEMENTATION: f"Ask about concrete implementation details, state management, or key libraries in {target_technology}.",
                CAT_TECH_CHOICE: f"Ask why {target_technology} was chosen for {target_proj_name or 'this system'} compared to alternatives, and what trade-offs were accepted.",
                CAT_DATABASE: f"Ask about database schema design, indexing, transactions, or query optimization in {target_proj_name or target_technology}.",
                CAT_API: f"Ask about REST/GraphQL API design, request validation, error status codes, or payload structuring in {target_proj_name or target_technology}.",
                CAT_SECURITY: f"Ask about authentication, authorization, token storage/revocation, or data protection in {target_proj_name or target_technology}.",
                CAT_DEBUGGING: f"Ask about a challenging technical bug, race condition, or edge case encountered while building with {target_technology}, and how it was resolved.",
                CAT_PERFORMANCE: f"Ask about performance bottlenecks, rendering optimizations, query latency, or caching in {target_proj_name or target_technology}.",
                CAT_TRADEOFFS: f"Ask what technical trade-offs, limitations, or architectural compromises were made in {target_proj_name or target_technology}.",
                CAT_ROLE_COMPETENCY: f"Ask an in-depth engineering competency question regarding {target_technology} in the context of {role_name}.",
            }
            spec_cat_goal = category_instructions.get(target_category, category_instructions[CAT_IMPLEMENTATION])

            resume_prompt = f"""
You are a senior technical interviewer for the role of {role_name}.
You have reviewed the candidate's resume and are testing whether they genuinely understand and built what they claim.

CANDIDATE'S VERIFIED RESUME DETAILS:
- Target Role: {role_name}
- Focus Project: {target_proj_name or "Resume project work"}
- Focus Technology: {target_technology}
- Target Question Category: {target_category} ({spec_cat_goal})
- Matched Skills: {", ".join(matched_skills[:8]) if matched_skills else "Technical background"}
- Matched Technologies: {", ".join(matched_technologies[:8]) if matched_technologies else target_technology}
- Matched Projects: {", ".join(str(p.get("name") if isinstance(p, dict) else p) for p in projects_inventory[:4])}

PROJECT EVIDENCE & EXCERPTS:
{evidence_block}

INTERVIEW PROGRESS:
- Current Target Topic: {target_technology or topic}
- Current Difficulty: {difficulty}
- Previous Questions Asked:
{chr(10).join(f"- {q}" for q in previous_questions) if previous_questions else "None (First Question)"}

STRICT INTERVIEWER RULES:
1. Ground the question DIRECTLY in what the candidate ACTUALLY built in their resume (e.g. "In your {target_proj_name or 'project'}, you utilized {target_technology}. How did you handle {target_category}...").
2. NEVER invent technologies, frameworks, or databases not mentioned in the resume.
3. NEVER ask generic textbook trivia (e.g. "What is Full Stack Development?", "What is polymorphism?").
4. Specifically address the question category: {target_category}.
5. Return ONLY valid JSON:
{{
    "question": "Your single personalized interview question here"
}}
"""
            try:
                from ai_engine.models.llm import llm
                if llm:
                    response = llm.invoke(resume_prompt)
                    raw_text = extract_llm_text(response)
                    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group(0))
                        q_text = parsed.get("question") or parsed.get("answer") or ""
                    else:
                        q_text = raw_text
                    q_text = q_text.strip().strip('"').strip("'")
                    if q_text and len(q_text) >= 15:
                        intent = detect_question_intent(q_text)
                        candidate_pool.append(QuestionCandidate(
                            text=q_text,
                            source=SOURCE_GEMINI_RESUME,
                            category=target_category,
                            topic=target_technology or topic,
                            intent=intent,
                            project=target_proj_name,
                            technology=target_technology,
                            difficulty=difficulty,
                            selection_reason=f"Probing {target_category} grounded in verified resume experience for {target_technology}."
                        ))
            except Exception as exc:
                logger.warning("Gemini resume question generation error: %s", exc)

        # --- Candidate C: Supabase Question Bank Retrieval (In role_phase or when exploring role competencies) ---
        if interview_phase != "resume_phase" or not has_resume:
            try:
                search_query = f"{role_name} {target_technology or topic} {target_category} {difficulty}"
                rag_result = self.rag.ask(
                    f"Select one practical technical interview question for {role_name} focusing on {target_technology or topic} and {target_category}.",
                    search_query=search_query,
                )
                if isinstance(rag_result, dict):
                    bank_q = rag_result.get("answer") or rag_result.get("question") or rag_result.get("text") or ""
                else:
                    bank_q = str(rag_result or "")
                bank_q = bank_q.strip().strip('"').strip("'")
                if bank_q and len(bank_q) >= 15:
                    intent = detect_question_intent(bank_q)
                    candidate_pool.append(QuestionCandidate(
                        text=bank_q,
                        source=SOURCE_SUPABASE_BANK,
                        category=target_category,
                        topic=target_technology or topic,
                        intent=intent,
                        project=target_proj_name,
                        technology=target_technology,
                        difficulty=difficulty,
                        selection_reason=f"Retrieved high-quality technical question for {target_technology} from verified question bank."
                    ))
            except Exception as exc:
                logger.warning("Supabase RAG retrieval error: %s", exc)

        # --- Candidate D: Missing Skill Question (Coverage-based trigger) ---
        unexplored_missing = [s for s in missing_skills if s not in missing_skills_covered]
        # Trigger when: resume topics are 40%+ explored OR strategy explicitly requests, and unexplored missing skills exist
        total_resume_items = len(projects_inventory) + len(technologies_inventory)
        explored_count = len(projects_covered) + len(technologies_covered)
        coverage_ratio = explored_count / max(1, total_resume_items)
        if unexplored_missing and has_resume and (coverage_ratio >= 0.4 or strategy == "missing_skill" or turn_count >= 3):
            target_missing = unexplored_missing[0]
            missing_skill_prompt = f"""
You are a senior technical interviewer for {role_name}.
The candidate's resume does NOT list experience with {target_missing}, which is an important requirement for {role_name}.

CANDIDATE'S KNOWN STACK:
- Projects: {", ".join(str(p.get("name") if isinstance(p, dict) else p) for p in projects_inventory[:3])}
- Technologies: {", ".join(technologies_inventory[:6])}

INTERVIEW GOAL:
Frame a realistic, hypothetical engineering scenario asking how the candidate would approach evaluating or integrating {target_missing} into their architecture.
Example framing: "Your project uses [Stack]. If you needed to integrate {target_missing} to solve [Problem], how would you design that integration and handle [Challenge]?"

STRICT RULES:
1. Do NOT claim the candidate already has experience with {target_missing}. Frame it explicitly as a hypothetical scenario or architectural extension.
2. Return ONLY valid JSON:
{{
    "question": "Your single hypothetical scenario question here"
}}
"""
            try:
                from ai_engine.models.llm import llm
                if llm:
                    response = llm.invoke(missing_skill_prompt)
                    raw_text = extract_llm_text(response)
                    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group(0))
                        q_text = parsed.get("question") or parsed.get("answer") or ""
                    else:
                        q_text = raw_text
                    q_text = q_text.strip().strip('"').strip("'")
                    if q_text and len(q_text) >= 15:
                        intent = detect_question_intent(q_text)
                        candidate_pool.append(QuestionCandidate(
                            text=q_text,
                            source=SOURCE_MISSING_SKILL,
                            category=CAT_MISSING_SKILL,
                            topic=target_missing,
                            intent=intent,
                            project=target_proj_name,
                            technology=target_missing,
                            difficulty=difficulty,
                            selection_reason=f"Assessing missing required role skill ({target_missing}) via hypothetical reasoning scenario."
                        ))
            except Exception as exc:
                logger.warning("Missing skill question generation error: %s", exc)

        # ------------------------------------------------------------------
        # 4. EVALUATE AND SCORE ALL CANDIDATES
        # ------------------------------------------------------------------
        evaluated_candidates: List[QuestionCandidate] = []
        for cand in candidate_pool:
            eval_cand = QuestionQualityEvaluator.evaluate(
                cand,
                role_name=role_name,
                verified_technologies=technologies_inventory,
                verified_projects=[p.get("name") if isinstance(p, dict) else str(p) for p in projects_inventory],
                unsupported_technologies=unsupported_technologies,
                missing_skills=missing_skills,
                previous_questions=previous_questions,
                recent_intents=recent_intents,
                categories_covered=categories_covered,
                projects_covered=projects_covered,
                technologies_covered=technologies_covered,
                last_answer=last_answer,
                strategy=strategy,
                target_difficulty=difficulty,
            )
            evaluated_candidates.append(eval_cand)

        # ------------------------------------------------------------------
        # 5. SELECT WINNING CANDIDATE & LOG DECISION
        # ------------------------------------------------------------------
        valid_candidates = [c for c in evaluated_candidates if c.is_valid]
        valid_candidates.sort(key=lambda c: c.score, reverse=True)

        if valid_candidates:
            winner = valid_candidates[0]
        else:
            # Deterministic category-aware fallback if all candidates failed validation
            fallback_text = controller.fallback(
                difficulty=difficulty,
                previous_questions=previous_questions,
                category=target_category,
                project_name=target_proj_name,
                technology=target_technology,
            )
            winner = QuestionCandidate(
                text=fallback_text,
                source=SOURCE_GEMINI_RESUME if has_resume else SOURCE_ROLE_BANK,
                category=target_category,
                topic=target_technology or topic,
                intent=detect_question_intent(fallback_text),
                project=target_proj_name,
                technology=target_technology,
                difficulty=difficulty,
                score=40.0,
                selection_reason=f"Deterministic fallback for category {target_category}."
            )

        # Step 24: Rich Debug Logging of Candidate Selection and Rejection Reasons
        rejected_candidates = [c for c in evaluated_candidates if c != winner]
        rejection_log = "\n".join(
            f"  - [{c.source}] Rejected: {c.rejection_reason or 'Lower ranking score (' + str(c.score) + ')'}"
            for c in rejected_candidates
        ) if rejected_candidates else "  - None"

        logger.info(
            "\n==================== [QUESTION SELECTION] ====================\n"
            "SELECTED QUESTION:\n"
            "  TEXT: %s\n"
            "  SOURCE: %s\n"
            "  ROLE: %s\n"
            "  PROJECT: %s\n"
            "  TECHNOLOGY: %s\n"
            "  CATEGORY: %s\n"
            "  INTENT: %s\n"
            "  DIFFICULTY: %s\n"
            "  QUALITY SCORE: %.2f\n"
            "  BREAKDOWN: role=%.1f, resume=%.1f, value=%.1f, novelty=%.1f, follow_up=%.1f, coverage=%.1f\n"
            "  WHY SELECTED: %s\n"
            "REJECTED CANDIDATES:\n%s\n"
            "=============================================================",
            winner.text,
            winner.source,
            role_name,
            winner.project or "N/A",
            winner.technology or "N/A",
            winner.category,
            winner.intent,
            winner.difficulty,
            winner.score,
            winner.role_relevance,
            winner.resume_relevance,
            winner.interview_value,
            winner.novelty,
            winner.answer_continuation_value,
            winner.coverage_value,
            winner.selection_reason or "Highest evaluated quality and context score",
            rejection_log,
        )

        return {
            "answer": winner.text,
            "source": winner.source,
            "category": winner.category,
            "intent": winner.intent,
            "topic": winner.topic,
            "project": winner.project,
            "technology": winner.technology,
            "why_selected": winner.selection_reason or f"Selected {winner.source} based on candidate state and technical evaluation.",
            "score": winner.score,
        }

