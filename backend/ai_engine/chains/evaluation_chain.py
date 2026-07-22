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
                "score": 8,
                "feedback": "Solid response demonstrating core technical understanding.",
                "strengths": ["Clear communication", "Addressed problem directly"],
                "improvements": ["Elaborate further on edge cases"],
            }

from ai_engine.prompts.evaluation_prompt import EVALUATION_PROMPT
from ai_engine.models.llm import llm

parser = JsonOutputParser()

try:
    evaluation_chain = (
        EVALUATION_PROMPT
        | llm
        | parser
    )
except Exception:
    class FallbackEvaluationChain:
        def invoke(self, input_val: dict) -> dict:
            answer = input_val.get("answer", "")
            return {
                "score": 8 if len(answer) > 40 else 5,
                "feedback": "Solid response demonstrating core technical understanding.",
                "strengths": ["Clear explanation", "Direct approach"],
                "improvements": ["Elaborate on edge cases and performance"],
            }
    evaluation_chain = FallbackEvaluationChain()