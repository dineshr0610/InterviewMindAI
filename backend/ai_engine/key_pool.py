import os
import time
import threading
import logging
import asyncio
from typing import List, Optional, Callable, TypeVar, Any, Awaitable

logger = logging.getLogger("interviewmind.ai_engine.key_pool")

from dotenv import load_dotenv
load_dotenv()

T = TypeVar("T")

class GeminiKeyPool:
    def __init__(self):
        self.lock = threading.Lock()
        
        self.keys: List[str] = []
        raw_keys = os.getenv("GEMINI_API_KEYS", "")
        if raw_keys:
            for k in raw_keys.split(","):
                k = k.strip()
                if k and k not in self.keys:
                    self.keys.append(k)
        
        if not self.keys:
            single_key = os.getenv("GEMINI_API_KEY", "").strip()
            if single_key:
                for k in single_key.split(","):
                    k = k.strip()
                    if k and k not in self.keys:
                        self.keys.append(k)
                
        self.current_index = 0
        self.cooldowns = {}
        
        # Configurable cooldowns
        self.transient_cooldown = int(os.getenv("GEMINI_KEY_TRANSIENT_COOLDOWN_SECONDS", "60"))
        self.quota_cooldown = int(os.getenv("GEMINI_KEY_QUOTA_COOLDOWN_SECONDS", "86400"))

        # 503/504/timeouts are usually model-wide, not per-key. Bound how many keys a single
        # call may burn through on such errors before giving up (callers then fall back).
        self.max_transient_failovers = max(1, int(os.getenv("GEMINI_MAX_TRANSIENT_FAILOVERS", "3")))

    def get_active_key(self, fail_fast: bool = False) -> str:
        while True:
            with self.lock:
                if not self.keys:
                    raise RuntimeError("No Gemini API keys configured. Please set GEMINI_API_KEYS.")
                
                self._recover_keys()
                
                start_index = self.current_index
                for i in range(len(self.keys)):
                    idx = (start_index + i) % len(self.keys)
                    if idx not in self.cooldowns:
                        self.current_index = idx
                        return self.keys[idx]
                
                earliest_recovery = min(self.cooldowns.values())
                wait_time = int(earliest_recovery - time.time())
                
                if fail_fast:
                    raise RuntimeError("All configured Gemini API keys are currently unavailable (fail_fast=True).")

                if wait_time > 0 and wait_time < 300:
                    logger.info(f"All keys on transient cooldown. Sleeping for {wait_time} seconds before retrying...")
                    # We must release the lock before sleeping so other threads can do things if necessary,
                    # but since this is inside a while loop, returning from the `with self.lock` block releases it.
                else:
                    raise RuntimeError(f"All configured Gemini API keys are currently unavailable. Try again in {wait_time} seconds.")
                    
            # Sleep outside the lock
            time.sleep(wait_time + 1)
            
    def _recover_keys(self):
        now = time.time()
        expired = [idx for idx, ts in self.cooldowns.items() if now >= ts]
        for idx in expired:
            del self.cooldowns[idx]
            
    def mark_exhausted(self, key_val: str, error_type: str):
        with self.lock:
            try:
                idx = self.keys.index(key_val)
                if idx not in self.cooldowns:
                    if error_type == "QUOTA":
                        duration = self.quota_cooldown
                    elif error_type in ("UNAVAILABLE", "TIMEOUT"):
                        duration = 10 # very short cooldown for 503/504
                    elif error_type == "AUTH_ERROR":
                        duration = 86400 * 365 # practically permanent
                    else:
                        duration = self.transient_cooldown
                    self.cooldowns[idx] = time.time() + duration
                    
                    if error_type == "QUOTA":
                        logger.warning(f"Gemini key index {idx} hit hard daily QUOTA; failing over for {duration}s.")
                    elif error_type == "UNAVAILABLE":
                        logger.warning(f"Gemini key index {idx} hit 503 UNAVAILABLE; failing over for {duration}s.")
                    elif error_type == "TIMEOUT":
                        logger.warning(f"Gemini key index {idx} hit 504 DEADLINE_EXCEEDED; failing over.")
                    elif error_type == "AUTH_ERROR":
                        logger.error(f"Gemini key index {idx} hit AUTH_ERROR (401/403); permanently failing over.")
                    else:
                        logger.warning(f"Gemini key index {idx} received transient rate-limit; failing over for {duration}s.")
            except ValueError:
                pass

    def classify_error(self, exc: Exception) -> Optional[str]:
        exc_name = type(exc).__name__
        exc_str = str(exc).lower()
        
        # Check for 401/403
        if "401" in exc_str or "403" in exc_str or "unauthorized" in exc_str or "forbidden" in exc_str or "api_key_invalid" in exc_str:
            return "AUTH_ERROR"
        
        # Check for 503 or overload explicitly
        if "503" in exc_str or "unavailable" in exc_str or "overloaded" in exc_str or "high demand" in exc_str:
            return "UNAVAILABLE"
            
        # Check for 504 or Timeout
        if "504" in exc_str or "deadline_exceeded" in exc_str or "deadline exceeded" in exc_str or exc_name == "TimeoutError" or "timeout" in exc_str or "timed out" in exc_str:
            return "TIMEOUT"
            
        # Check for explicit daily/hard quota exhaustion first
        if "per day" in exc_str or "requests per day" in exc_str or "generaterequestsperday" in exc_str:
            return "QUOTA"
            
        # Check for explicit minute/transient limits
        if "per minute" in exc_str or "requests per minute" in exc_str:
            return "TRANSIENT"
            
        # If it says 'quota' but doesn't mention minutes, assume hard quota
        if "quota" in exc_str and "per minute" not in exc_str:
            return "QUOTA"
            
        if "rate limit" in exc_str or "too many requests" in exc_str or "429" in exc_str:
            return "TRANSIENT"
            
        # Fallback to exception types
        if exc_name == "ResourceExhausted":
            if "quota" in exc_str:
                return "QUOTA"
            return "TRANSIENT"
            
        if "google.api_core.exceptions" in str(type(exc)):
            if exc_name == "TooManyRequests":
                return "TRANSIENT"
            if exc_name == "ResourceExhausted":
                if "quota" in exc_str:
                    return "QUOTA"
                return "TRANSIENT"
                
        if exc_name == "APIError":
            if hasattr(exc, "code") and exc.code == 429:
                return "TRANSIENT"
            if "429" in exc_str:
                return "TRANSIENT"
                
        if "resource_exhausted" in exc_str:
            if "quota" in exc_str:
                return "QUOTA"
            return "TRANSIENT"
            
        return None
        
    def execute_with_fallback(self, func: Callable[[str], T], max_retries: int = None, fail_fast: bool = False) -> T:
        max_attempts = max_retries if max_retries is not None else 1000000
        last_exception = None
        transient_failures = 0
        
        for attempt in range(max_attempts):
            active_key = self.get_active_key(fail_fast=fail_fast)
            idx = self.keys.index(active_key)
            try:
                if attempt == 0:
                    logger.debug(f"Gemini request using key index {idx}")
                else:
                    logger.info(f"Gemini request retrying with key index {idx}")
                return func(active_key)
            except Exception as e:
                last_exception = e
                err_type = self.classify_error(e)
                if err_type:
                    self.mark_exhausted(active_key, err_type)
                    if err_type in ("UNAVAILABLE", "TIMEOUT"):
                        transient_failures += 1
                        if transient_failures >= self.max_transient_failovers:
                            raise RuntimeError(
                                f"Gemini service unavailable after {transient_failures} consecutive 503/504/timeout responses; "
                                "not trying remaining keys."
                            ) from e
                else:
                    raise e
                    
        raise RuntimeError("All configured Gemini API keys are currently unavailable.") from last_exception

    async def aexecute_with_fallback(self, func: Callable[[str], Awaitable[T]], max_retries: int = None, fail_fast: bool = False) -> T:
        if max_retries is None:
            max_retries = len(self.keys) if self.keys else 1
            
        max_attempts = min(max_retries, len(self.keys) * 2) 
        last_exception = None
        transient_failures = 0
        
        for attempt in range(max_attempts):
            active_key = self.get_active_key(fail_fast=fail_fast)
            idx = self.keys.index(active_key)
            try:
                if attempt == 0:
                    logger.debug(f"Gemini request using key index {idx}")
                else:
                    logger.info(f"Gemini request retrying with key index {idx}")
                return await func(active_key)
            except Exception as e:
                last_exception = e
                err_type = self.classify_error(e)
                if err_type:
                    self.mark_exhausted(active_key, err_type)
                    if err_type in ("UNAVAILABLE", "TIMEOUT"):
                        transient_failures += 1
                        if transient_failures >= self.max_transient_failovers:
                            raise RuntimeError(
                                f"Gemini service unavailable after {transient_failures} consecutive 503/504/timeout responses; "
                                "not trying remaining keys."
                            ) from e
                else:
                    raise e
                    
        raise RuntimeError("All configured Gemini API keys are currently unavailable.") from last_exception

gemini_key_pool = GeminiKeyPool()
