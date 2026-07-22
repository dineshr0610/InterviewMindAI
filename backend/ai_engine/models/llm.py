"""
Gemini LLM initialization reading GEMINI_API_KEY from environment variables.
"""

from __future__ import annotations

import os
import importlib
import logging
from typing import Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("interviewmind.ai_engine.llm")

api_key = os.getenv("GEMINI_API_KEY")

llm: Any = None
if api_key and api_key.strip():
    try:
        genai_mod = importlib.import_module("langchain_google_genai")
        ChatGoogleGenerativeAI = getattr(genai_mod, "ChatGoogleGenerativeAI")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key.strip(),
            temperature=0
        )
        logger.info("ChatGoogleGenerativeAI initialized successfully with GEMINI_API_KEY.")
    except Exception as exc:
        logger.warning("Failed to initialize ChatGoogleGenerativeAI: %s. Using fallback LLM.", exc)

if llm is None:
    class FallbackLLM:
        def invoke(self, input_val: Any) -> str:
            return "Please configure GEMINI_API_KEY in backend/.env to enable live Gemini AI generation."
        def __or__(self, other: Any):
            class PipeLLM:
                def __init__(self, first, second):
                    self.first = first
                    self.second = second
                def invoke(self, val):
                    res = self.first.invoke(val)
                    if hasattr(second := self.second, 'invoke'):
                        return second.invoke(res)
                    return res
            return PipeLLM(self, other)
        def __ror__(self, other: Any):
            class PipeRLLM:
                def __init__(self, first, second):
                    self.first = first
                    self.second = second
                def invoke(self, val):
                    return self.second.invoke(val)
            return PipeRLLM(other, self)

    llm = FallbackLLM()