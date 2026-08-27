from __future__ import annotations

import re


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
