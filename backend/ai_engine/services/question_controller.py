from __future__ import annotations

import re

# Conversational next-question strategies. These are guidance, not rigid
# scripts: the generation prompt uses them to decide what a real interviewer
# would ask next given the candidate's last answer.
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

# How many consecutive related questions before the interviewer should
# generally move to another relevant topic (see follow_up_depth guards).
MAX_FOLLOW_UP_DEPTH = 2

# Strategies that continue the current topic (count toward follow_up_depth).
DEEPENING_STRATEGIES = {
    FOLLOW_UP,
    CLARIFICATION,
    DEEPER_PROBE,
    EDGE_CASE,
    TRADEOFF,
    SCENARIO,
    ARCHITECTURE,
}


def choose_next_strategy(score: int, follow_up_depth: int = 0) -> str:
    """Choose the most appropriate next-interview action for the last answer.

    - High score (>= 8): the candidate demonstrated strong understanding, so
      push deeper (tradeoffs, edge cases, scaling, architecture).
    - Medium score (5-7): reasonable but incomplete, so clarify / follow up.
    - Low score (<= 4): struggling, so simplify, test fundamentals and give
      them a chance to recover.
    - If we have already probed the same subject deeply enough, transition to
      another relevant topic to keep the interview balanced.
    """
    if follow_up_depth >= MAX_FOLLOW_UP_DEPTH:
        return TOPIC_TRANSITION

    if score >= 8:
        # Alternate between deepening tactics to avoid repetitive templates.
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


# Question diversity: guide the AI away from repeatedly asking "Explain X".
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


class AdaptiveQuestionController:

    def __init__(self, topic: str):
        self.topic = topic

        self.concepts = [
            ("definition", f"What is {topic}, and why is it useful?"),
            ("mechanism", f"How does {topic} work step by step, and how does it reduce the search space?"),
            ("implementation", f"When implementing {topic}, what are the key variables or operations you must handle correctly?"),
            ("complexity", f"What are the time and space complexities of {topic}, and why?"),
            ("edge_cases", f"What important edge cases should you consider when implementing {topic}?"),
        ]

    def choose_focus(self, difficulty: str, previous_questions: list[str]) -> str:
        text = " ".join(previous_questions).lower()

        if not any(x in text for x in ["what is", "define", "definition"]):
            return "definition"

        if not any(x in text for x in ["how does", "work", "process", "search space"]):
            return "mechanism"

        if not any(x in text for x in ["implement", "pointer", "variable", "operation"]):
            return "implementation"

        if not any(x in text for x in ["complexit", "o(log", "o(1)", "o(n)"]):
            return "complexity"

        return "edge_cases"

    def fallback(
        self,
        difficulty: str = "Medium",
        previous_questions: list[str] | None = None,
    ) -> str:
        previous_questions = previous_questions or []
        previous = " ".join(previous_questions).lower()

        for concept, question in self.concepts:
            keywords = {
                "definition": ["what is", "define", "useful"],
                "mechanism": ["how does", "work", "search space"],
                "implementation": ["implement", "pointer", "variable", "operation"],
                "complexity": ["complexit", "o(log", "o(1)", "o(n)"],
                "edge_cases": ["edge case", "empty", "duplicate", "missing"],
            }[concept]

            if not any(k in previous for k in keywords):
                return question

        return (
            f"Give a practical {difficulty} example of {self.topic}, "
            f"explain the approach, and discuss its complexity."
        )

    def validate(
        self,
        question: str,
        previous_questions: list[str] | None = None,
    ):
        previous_questions = previous_questions or []

        if not question or len(question.strip()) < 15:
            return False, "empty"

        q = question.lower().strip()

        if self.topic.lower() not in q:
            return False, "topic_missing"

        for previous in previous_questions:
            p = previous.lower().strip()

            if q == p:
                return False, "duplicate"

            # Detect near-duplicate questions.
            q_words = set(re.findall(r"\b[a-z0-9]+\b", q))
            p_words = set(re.findall(r"\b[a-z0-9]+\b", p))

            if q_words and p_words:
                similarity = len(q_words & p_words) / max(
                    1, len(q_words | p_words)
                )

                if similarity >= 0.75:
                    return False, "near_duplicate"

        return True, "valid"
