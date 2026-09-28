"""
Direct dynamic technical question generation chain without vector DB lookup.
"""

from __future__ import annotations

import importlib
from typing import Any, Dict

try:
    parsers_mod = importlib.import_module("langchain_core.output_parsers")
    JsonOutputParser = getattr(parsers_mod, "JsonOutputParser")
except ImportError:
    class JsonOutputParser:
        def invoke(self, input_val: Any) -> Dict:
            if isinstance(input_val, dict):
                return input_val
            return {
                "answer": "Can you explain the core architectural principles and trade-offs in your technical stack?"
            }

from ai_engine.prompts.question_prompt import QUESTION_PROMPT
from ai_engine.models.llm import llm

parser = JsonOutputParser()

try:
    question_chain = (
        QUESTION_PROMPT
        | llm
        | parser
    )
except Exception:
    class FallbackQuestionChain:
        def invoke(self, input_val: dict) -> dict:
            topic = input_val.get("topic", "Software Engineering")
            difficulty = input_val.get("difficulty", "Medium")
            return {
                "answer": f"Given a production system in {topic}, how would you approach performance optimization and reliability at a {difficulty} level?"
            }
    question_chain = FallbackQuestionChain()
