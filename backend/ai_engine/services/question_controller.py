from __future__ import annotations

import re
from typing import List, Optional

# Conversational next-question strategies
FOLLOW_UP = "follow_up"
CLARIFICATION = "clarification"
DEEPER_PROBE = "deeper_probe"
EDGE_CASE = "edge_case"
TRADEOFF = "tradeoff"
SCENARIO = "scenario"
ARCHITECTURE = "architecture"
FUNDAMENTALS = "fundamentals"
PROBLEM_SOLVING = "problem_solving"
TOPIC_TRANSITION = "topic_transition"

MAX_FOLLOW_UP_DEPTH = 2

DEEPENING_STRATEGIES = {
    FOLLOW_UP,
    CLARIFICATION,
    DEEPER_PROBE,
    EDGE_CASE,
    TRADEOFF,
    SCENARIO,
    ARCHITECTURE,
}

# Standardized Question Categories across the interview pool
CAT_ARCHITECTURE = "architecture"
CAT_DATA_FLOW = "data_flow"
CAT_IMPLEMENTATION = "implementation"
CAT_TECH_CHOICE = "tech_choice"
CAT_DATABASE = "database_design"
CAT_API = "api_design"
CAT_SECURITY = "security_auth"
CAT_DEBUGGING = "debugging_edge_cases"
CAT_PERFORMANCE = "performance_scalability"
CAT_TRADEOFFS = "trade_offs"
CAT_ROLE_COMPETENCY = "role_competency"
CAT_MISSING_SKILL = "missing_skill"
CAT_FOLLOW_UP = "follow_up"

ALL_QUESTION_CATEGORIES = [
    CAT_ARCHITECTURE,
    CAT_DATA_FLOW,
    CAT_IMPLEMENTATION,
    CAT_TECH_CHOICE,
    CAT_DATABASE,
    CAT_API,
    CAT_SECURITY,
    CAT_DEBUGGING,
    CAT_PERFORMANCE,
    CAT_TRADEOFFS,
    CAT_ROLE_COMPETENCY,
    CAT_MISSING_SKILL,
    CAT_FOLLOW_UP,
]

CATEGORY_QUESTION_TEMPLATES = {
    CAT_ARCHITECTURE: [
        "Can you walk me through the architecture of {subject} and explain how the components interact?",
        "How did you structure the architecture of {subject} for maintainability and separation of concerns?",
    ],
    CAT_DATA_FLOW: [
        "How does data flow end-to-end in {subject}, from the client request through the API down to data persistence?",
        "Can you trace the exact lifecycle of a request in {subject} and explain how state updates are handled?",
    ],
    CAT_IMPLEMENTATION: [
        "When implementing {subject}, what specific patterns, hooks, or libraries did you utilize and why?",
        "What were the most challenging implementation details or state management complexities you handled in {subject}?",
    ],
    CAT_TECH_CHOICE: [
        "Why did you choose {subject} over alternative technologies or frameworks for this use case?",
        "What specific capabilities of {subject} made it the right choice compared to other options?",
    ],
    CAT_DATABASE: [
        "How did you design the database schema and handle queries/indexing in {subject}?",
        "How did you handle database transactions, data consistency, and query optimization in {subject}?",
    ],
    CAT_API: [
        "When designing the backend APIs for {subject}, how did you handle request validation, error handling, and status codes?",
        "How did you structure your API endpoints and handle authentication/authorization in {subject}?",
    ],
    CAT_SECURITY: [
        "How did you implement authentication, authorization, and secure token/credential handling in {subject}?",
        "What security considerations (such as CORS, input sanitization, or rate limiting) did you put in place for {subject}?",
    ],
    CAT_DEBUGGING: [
        "What was a difficult technical bug, edge case, or production issue you encountered with {subject}, and how did you troubleshoot it?",
        "What error handling or failure recovery mechanisms did you implement to prevent system failures in {subject}?",
    ],
    CAT_PERFORMANCE: [
        "If user traffic or data volume on {subject} increased tenfold, what would become the primary bottleneck and how would you optimize it?",
        "What caching strategies, query optimizations, or rendering performance improvements did you implement for {subject}?",
    ],
    CAT_TRADEOFFS: [
        "What technical trade-offs, limitations, or compromises did you encounter when building with {subject}?",
        "Looking back, what would you re-architect or change about how {subject} was implemented?",
    ],
    CAT_ROLE_COMPETENCY: [
        "Can you explain how {subject} works under the hood and how it applies to real-world production engineering?",
        "What are the best practices and common pitfalls when developing systems with {subject}?",
    ],
    CAT_MISSING_SKILL: [
        "If you were tasked with integrating {subject} into your architecture, how would you design the integration and handle potential edge cases?",
    ],
    CAT_FOLLOW_UP: [
        "Building on what you mentioned about {subject}, can you explain the technical trade-offs and how you handle failure scenarios?",
    ],
}


def choose_next_strategy(score: int, follow_up_depth: int = 0) -> str:
    """Choose the most appropriate next-interview action for the last answer."""
    if follow_up_depth >= MAX_FOLLOW_UP_DEPTH:
        return TOPIC_TRANSITION

    if score >= 8:
        return [
            DEEPER_PROBE,
            EDGE_CASE,
            TRADEOFF,
            SCENARIO,
            ARCHITECTURE,
        ][follow_up_depth % 5]
    if score >= 5:
        return [
            FOLLOW_UP,
            CLARIFICATION,
            DEEPER_PROBE,
        ][follow_up_depth % 3]
    return [
        FUNDAMENTALS,
        CLARIFICATION,
        FOLLOW_UP,
    ][follow_up_depth % 3]


DIVERSITY_PROMPTS = {
    FOLLOW_UP: "Ask a focused follow-up that references the candidate's last answer.",
    CLARIFICATION: "Ask a clarifying question about an underdeveloped part of the candidate's last answer.",
    DEEPER_PROBE: "Probe deeper into a specific, interesting claim or concept in the candidate's last answer.",
    EDGE_CASE: "Ask about an important edge case or failure condition related to what the candidate just described.",
    TRADEOFF: "Ask about the trade-offs, limitations, or alternatives of the approach the candidate described.",
    SCENARIO: "Pose a realistic production scenario or scaling situation building on the candidate's last answer.",
    ARCHITECTURE: "Ask how the technique or system the candidate described fits into a larger system or architecture.",
    FUNDAMENTALS: "Re-visit the fundamental concept in a simpler way so the candidate has a chance to recover.",
    PROBLEM_SOLVING: "Ask a practical problem-solving question using the concepts the candidate just discussed.",
    TOPIC_TRANSITION: "Naturally transition to another relevant aspect of the role/topic that has not been covered yet.",
}


# Standard Question Intents across interview turns
INTENT_EXPLAIN = "explain"
INTENT_DESIGN = "design"
INTENT_IMPLEMENT = "implement"
INTENT_DEBUG = "debug"
INTENT_COMPARE = "compare"
INTENT_JUSTIFY = "justify"
INTENT_OPTIMIZE = "optimize"
INTENT_DIAGNOSE = "diagnose"
INTENT_PREDICT = "predict"
INTENT_TRADEOFF = "tradeoff"
INTENT_SCENARIO = "scenario"
INTENT_ARCHITECTURE = "architecture"
INTENT_REASONING = "reasoning"
INTENT_EXPERIENCE = "experience"
INTENT_FUNDAMENTALS = "fundamentals"

ALL_QUESTION_INTENTS = [
    INTENT_EXPLAIN,
    INTENT_DESIGN,
    INTENT_IMPLEMENT,
    INTENT_DEBUG,
    INTENT_COMPARE,
    INTENT_JUSTIFY,
    INTENT_OPTIMIZE,
    INTENT_DIAGNOSE,
    INTENT_PREDICT,
    INTENT_TRADEOFF,
    INTENT_SCENARIO,
    INTENT_ARCHITECTURE,
    INTENT_REASONING,
    INTENT_EXPERIENCE,
    INTENT_FUNDAMENTALS,
]


def detect_question_intent(question_text: str) -> str:
    """Classify the technical intent of an interview question."""
    if not question_text:
        return INTENT_EXPLAIN
    q = question_text.lower()
    
    if any(k in q for k in ["why did you choose", "what led you", "reason for picking", "rationale behind", "justify", "why select"]):
        return INTENT_JUSTIFY
    if any(k in q for k in ["trade-off", "tradeoff", "compromise", "drawback", "limitation", "pros and cons", "downsides"]):
        return INTENT_TRADEOFF
    if any(k in q for k in ["what happens if", "suppose", "if user traffic", "scenario", "imagine", "if two users", "if two concurrent", "concurrent transactions", "conflict", "race condition", "traffic increased"]):
        return INTENT_SCENARIO
    if any(k in q for k in ["how did you design", "schema design", "database schema", "model", "endpoint design", "how did you structure", "structure your"]):
        return INTENT_DESIGN
    if any(k in q for k in ["optimize", "optimizing", "index", "indexing", "bottleneck", "latency", "throughput", "caching", "cache", "performance", "improve this query"]):
        return INTENT_OPTIMIZE
    if any(k in q for k in ["bug", "troubleshoot", "debug", "failure", "error", "exception", "failure recovery", "edge case", "production issue"]):
        return INTENT_DEBUG
    if any(k in q for k in ["compare", "difference between", "versus", " vs ", "over alternative"]):
        return INTENT_COMPARE
    if (
        any(k in q for k in ["architecture", "high-level", "system overview", "component boundaries", "walk me through the architecture", "components interact", "components are structured", "structure the architecture", "are structured"])
        or bool(re.search(r"components.*(?:structure|interact|boundar)", q))
    ):
        return INTENT_ARCHITECTURE
    if any(k in q for k in ["how did you implement", "code", "hooks", "function", "library", "pattern", "syntax", "implementation details", "how does a request move", "data flow"]):
        return INTENT_IMPLEMENT
    if any(k in q for k in ["what is", "how does", "define", "concept of", "core principle", "under the hood"]):
        return INTENT_FUNDAMENTALS
    if any(k in q for k in ["how would you evaluate", "how would you assess", "reasoning", "decision", "how would you evaluate whether"]):
        return INTENT_REASONING
    if any(k in q for k in ["in your experience", "in your project", "have you worked"]):
        return INTENT_EXPERIENCE
    return INTENT_EXPLAIN


class AdaptiveQuestionController:

    def __init__(self, topic: str):
        self.topic = topic

    def choose_focus(self, difficulty: str, previous_questions: list[str]) -> str:
        text = " ".join(previous_questions).lower()
        if not previous_questions:
            return "definition"
        if not any(x in text for x in ["how does", "mechanism", "work step by step", "architecture"]):
            return "mechanism"
        if not any(x in text for x in ["implement", "code", "function", "pattern", "library"]):
            return "implementation"
        if not any(x in text for x in ["edge case", "bug", "error", "null", "failure"]):
            return "edge_cases"
        return "tradeoffs"

    def fallback(
        self,
        difficulty: str = "Medium",
        previous_questions: list[str] | None = None,
        category: str | None = None,
        project_name: str | None = None,
        technology: str | None = None,
    ) -> str:
        previous_questions = previous_questions or []
        subject = project_name or technology or self.topic
        
        if category and category in CATEGORY_QUESTION_TEMPLATES:
            templates = CATEGORY_QUESTION_TEMPLATES[category]
            for template in templates:
                cand = template.format(subject=subject)
                if not any(cand.lower() == p.lower() for p in previous_questions):
                    return cand

        # Default progressive templates
        templates = [
            f"What is {subject}, and how did you apply it in your project?",
            f"How does {subject} work under the hood, and what are its key components?",
            f"When implementing {subject}, what specific patterns, hooks, or libraries did you utilize?",
            f"What edge cases, error handling, or performance challenges did you encounter in {subject}?",
            f"What are the main technical trade-offs of using {subject} compared to alternative approaches?",
        ]
        for cand in templates:
            if not any(cand.lower() == p.lower() for p in previous_questions):
                return cand

        return f"In your technical experience with {subject}, what were the key architecture decisions and trade-offs you made?"

    def validate(
        self,
        question: str,
        previous_questions: list[str] | None = None,
        resume_context: str | None = None,
        target_subject: str | None = None,
        unsupported_technologies: list[str] | None = None,
    ) -> tuple[bool, str]:
        previous_questions = previous_questions or []

        if not question or len(question.strip()) < 15:
            return False, "empty"

        q = question.lower().strip()

        # 1. Exact string duplicate
        for previous in previous_questions:
            p = previous.lower().strip()
            if q == p:
                return False, "duplicate"

            # 2. Token overlap similarity
            q_words = set(re.findall(r"\b[a-z0-9]+\b", q))
            p_words = set(re.findall(r"\b[a-z0-9]+\b", p))
            if q_words and p_words:
                similarity = len(q_words & p_words) / max(1, len(q_words | p_words))
                if similarity >= 0.70:
                    return False, "near_duplicate"

        # 3. Hallucination check: Unsupported claims asserting experience (run before topic missing)
        if unsupported_technologies:
            for unsupp in unsupported_technologies:
                u_term = unsupp.lower().strip()
                if u_term and u_term in q:
                    is_claiming = any(
                        cl in q
                        for cl in [
                            "you implemented",
                            "you built",
                            "you used",
                            "you deployed",
                            "you designed",
                            "you created",
                            "in your portfolio",
                            "in your resume",
                            "your experience with",
                            "highlight experience with",
                            f"in your {u_term}",
                            f"your {u_term} project",
                        ]
                    ) or bool(re.search(rf"\byou\s+(?:implemented|built|used|deployed|configured)\s+(?:a\s+|an\s+|the\s+)?{re.escape(u_term)}", q))
                    
                    is_hypothetical = any(
                        hyp in q
                        for hyp in [
                            "if you needed",
                            "hypothetical",
                            "suppose",
                            "does not mention",
                            "would you evaluate",
                            "if you were tasked",
                        ]
                    )
                    if is_claiming and not is_hypothetical:
                        return False, "unsupported_claim"

        # 4. Semantic repetition check: (same subject/project/tech + same intent or related intent)
        cand_intent = detect_question_intent(question)
        if target_subject and previous_questions:
            subj_lower = target_subject.lower()
            for prev_q in previous_questions:
                prev_lower = prev_q.lower()
                if (subj_lower in q and subj_lower in prev_lower) or any(
                    tok in q and tok in prev_lower for tok in subj_lower.split() if len(tok) > 3
                ):
                    prev_intent = detect_question_intent(prev_q)
                    # Same intent or architecture/design equivalence on the same project/topic is a semantic duplicate
                    intents_match = (
                        cand_intent == prev_intent
                        or {cand_intent, prev_intent} <= {INTENT_ARCHITECTURE, INTENT_DESIGN}
                    )
                    if intents_match and (cand_intent in (
                        INTENT_ARCHITECTURE,
                        INTENT_DESIGN,
                        INTENT_JUSTIFY,
                        INTENT_TRADEOFF,
                        INTENT_DEBUG,
                    ) or prev_intent in (
                        INTENT_ARCHITECTURE,
                        INTENT_DESIGN,
                        INTENT_JUSTIFY,
                        INTENT_TRADEOFF,
                        INTENT_DEBUG,
                    )):
                        return False, "semantic_repetition"

        # 5. Topic alignment check
        if self.topic and not resume_context:
            topic_tokens = [t for t in re.findall(r"\b[a-z0-9]+\b", self.topic.lower()) if len(t) > 2]
            if topic_tokens and not any(token in q for token in topic_tokens):
                return False, "topic_missing"

        return True, "valid"


