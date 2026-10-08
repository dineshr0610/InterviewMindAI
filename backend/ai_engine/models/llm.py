"""
Gemini LLM initialization reading GEMINI_API_KEY from environment variables.
"""

from __future__ import annotations

import os
import importlib
import logging
from typing import Any, Optional
from dotenv import load_dotenv

from langchain_core.runnables import Runnable, RunnableConfig
from ai_engine.key_pool import gemini_key_pool

load_dotenv()
logger = logging.getLogger("interviewmind.ai_engine.llm")

model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

class PoolableLLM(Runnable):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.genai_mod = importlib.import_module("langchain_google_genai")
        self.ChatGoogleGenerativeAI = getattr(self.genai_mod, "ChatGoogleGenerativeAI")
        
    def _get_llm(self, key: str, timeout: Optional[float] = None):
        return self.ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=key,
            temperature=0,
            max_retries=0, # Disable SDK retries to let GeminiKeyPool handle failover
            timeout=timeout
        )

    def invoke(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Any:
        timeout = kwargs.pop("timeout", None)
        pool_max_retries = kwargs.pop("pool_max_retries", None)
        fail_fast = kwargs.pop("fail_fast", False)
        def do_invoke(key):
            llm = self._get_llm(key, timeout=timeout)
            return llm.invoke(input, config=config, **kwargs)
        return gemini_key_pool.execute_with_fallback(do_invoke, max_retries=pool_max_retries, fail_fast=fail_fast)

    async def ainvoke(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Any:
        timeout = kwargs.pop("timeout", None)
        pool_max_retries = kwargs.pop("pool_max_retries", None)
        fail_fast = kwargs.pop("fail_fast", False)
        async def do_ainvoke(key):
            llm = self._get_llm(key, timeout=timeout)
            return await llm.ainvoke(input, config=config, **kwargs)
        return await gemini_key_pool.aexecute_with_fallback(do_ainvoke, max_retries=pool_max_retries, fail_fast=fail_fast)

# FallbackLLM for missing keys
class FallbackLLM(Runnable):
    def invoke(self, input_val: Any, config: Optional[RunnableConfig] = None, **kwargs: Any) -> str:
        return "Please configure GEMINI_API_KEYS in backend/.env to enable live Gemini AI generation."
    
    async def ainvoke(self, input_val: Any, config: Optional[RunnableConfig] = None, **kwargs: Any) -> str:
        return "Please configure GEMINI_API_KEYS in backend/.env to enable live Gemini AI generation."

if gemini_key_pool.keys:
    llm = PoolableLLM(model_name)
    logger.info("PoolableLLM initialized successfully with model '%s'.", model_name)
else:
    llm = FallbackLLM()
    logger.warning("No Gemini API keys found. Using FallbackLLM.")
