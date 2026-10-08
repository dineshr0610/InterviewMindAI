# Resume AI Failure Handling (Phase 4A Hotfix)

This document details the configuration and architecture changes implemented to ensure the system gracefully handles Gemini API quotas, rate-limits, and provider unavailability, specifically during AI Resume Analysis.

## 1. 429 Daily Quota Behavior (Hard Quota)
- **Classification:** Errors containing `"per day"` or `"requests per day"` are now explicitly classified as `QUOTA` in `GeminiKeyPool`.
- **Handling:** When a key hits its daily hard limit, the key pool registers a long cooldown (86400s) for that specific key. 
- **SDK Overrides:** `max_retries=0` is configured in `ChatGoogleGenerativeAI` to bypass the SDK's exponential backoff, allowing the `GeminiKeyPool` to fail over immediately without blocking the thread for 60-120 seconds.

## 2. 429 Per-Minute Behavior (Transient Rate-Limit)
- **Classification:** Errors with `"per minute"`, `"429"`, or `"rate limit"` are classified as `TRANSIENT`.
- **Handling:** Handled by standard `transient_cooldown` (60s). The `GeminiKeyPool` attempts the next available key immediately.

## 3. 503 UNAVAILABLE Behavior (Model Overload)
- **Classification:** Errors containing `"503"`, `"unavailable"`, `"overloaded"`, or `"high demand"` are now explicitly captured and classified as `UNAVAILABLE`.
- **Handling:** Instead of treating 503s as daily quotas or standard transient limits, they now trigger a dedicated, short 10-second cooldown on the affected key before trying the next key in the pool.

## 4. Key-Pool & Fail-Fast Behavior
- **Timeout & Retry Limits:** For resume analysis, `PoolableLLM` now accepts `fail_fast=True` and `pool_max_retries` bounded to the number of configured keys.
- **Immediate Fallback:** If all keys are on cooldown due to successive quota exhaustion or 503 errors, `get_active_key(fail_fast=True)` throws immediately rather than sleeping. This guarantees fallback to deterministic analysis within ~5-15 seconds rather than minutes.

## 5. `NoneType.lower()` Root Cause & Safe Normalization
- **Issue:** The crash occurred in `_is_valid()` when `topic` (requirement name) or evidence items returned by Gemini were `null`, resulting in `NoneType` method calls (`None.lower()`).
- **Fix:** Implemented safe type-casting (`str(topic)`) and null checks. Missing/unknown fields are skipped rather than causing pipeline failure.
- **Validation:** Added robust structural checks (e.g., verifying `ai_data` is a `dict`, and iterating over `list` structures safely) before parsing any Gemini response. Confidence values are safely clamped to `[0.0, 1.0]`.

## 6. Deterministic vs AI Matches
- Deterministic matches are authoritative and computed first.
- Gemini enhancements are additive. If Gemini hallucinated projects or missing evidence, they are discarded (`_is_valid()` verifies the evidence against `raw_text`).
- If AI analysis completes successfully, `analysis_source` is set to `"hybrid"`. If Gemini is completely unavailable, `analysis_source` is `"deterministic"`.

## 7. Test Results
- **9/9 tests passed** in `test_ai_resume_analyzer.py`, verifying:
  - Daily quota fallback
  - Safe normalization of nulls/non-strings
  - Rejection of hallucinated evidence and unknown projects
  - Clamping of confidence > 1.0
  - Fallback on malformed JSON
- **Integration Test Passed:** The pipeline correctly skipped adding `"Unknown"` requirement matches.

## 8. Controlled Live Validation Result
- Tested against the 12 configured keys. Keys 0, 1, 2 failed due to hard `QUOTA`. Keys 3-10 hit `503 UNAVAILABLE` and smoothly failed over.
- **Performance:** Iterated through 11 keys in **~51 seconds** (average <5s per request/retry cycle), successfully yielding a `hybrid` analysis using Key 11.
- **Data Integrity:** Produced accurate `hybrid` output matching all 11 valid role skills safely and preserving the deterministic baseline score (55.8).
