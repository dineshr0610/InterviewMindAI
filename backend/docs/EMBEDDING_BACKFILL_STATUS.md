# Embedding Backfill Status

**Date:** October 5, 2026

## Current Status
- **Total Rows in `document_embeddings`:** 9,394
- **Embedded Rows:** 236
- **Missing Embeddings (Remaining):** 9,158
- **Invalid Dimensions (!= 1536):** 0

## Configuration
- **Embedding Model:** `gemini-embedding-2`
- **Expected Dimensions:** 1536
- **Max Concurrent Workers:** Configurable via `GEMINI_EMBEDDING_MAX_WORKERS` (default: 10)
- **Key Pool:** Used `GeminiKeyPool` for fallback and rate limiting

## Last Run Summary
- **Processed:** 220 rows
- **Failed / Aborted:** Cleanly aborted on API Quota limit.
- **Reason for Stop:** `429 Too Many Requests (QUOTA)`. All configured keys within the pool received strict daily quota limits or transient cooldowns, halting execution safely.

## Next Action
- Wait for Gemini API quotas to reset (typically 24 hours from exhaustion).
- Run `python scripts/backfill_embeddings.py --limit 10000 --batch-size 50` to resume. The script will automatically skip the 236 already embedded rows and resume on the 9,158 missing rows.
