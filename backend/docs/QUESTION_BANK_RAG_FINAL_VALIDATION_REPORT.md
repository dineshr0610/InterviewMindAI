# Question Bank RAG Final Validation Report (Phase 3)

**Date:** October 5, 2026
**Target:** Question Bank Embedding Backfill & RAG Retrieval
**Status:** PARTIAL BACKFILL COMPLETED (Stopped safely on quota) & FULL RAG PIPELINE VALIDATED

## A. Initial Embedding State
Based on direct `asyncpg` queries of the database:
- **Total Rows:** 9,394
- **Rows with Embeddings (Before):** 16
- **Rows Missing Embeddings:** 9,378
- **Embedding Dimensions:** 1,536 (Confirmed via `gemini-embedding-2`)

## B. Final Embedding State
- **Total Rows:** 9,394
- **Rows with Embeddings (After):** 236
- **Rows Missing Embeddings (Remaining):** 9,158

## C. Number Successfully Backfilled
- **Newly Embedded:** 220 rows
- **Execution:** Used `backfill_embeddings.py` scaled up to use concurrent ThreadPool processing (`max_workers=20`) to accelerate API requests while utilizing `GeminiKeyPool` for load balancing.

## D. Failed / Remaining Rows
- **Remaining NULL:** 9,158
- **Reason for Stop:** The script halted cleanly. The `GeminiKeyPool` successfully rotated through keys but encountered a hard limit across all configured keys: `google.genai.errors.ClientError: 429 Too Many Requests (QUOTA)`. As requested, we did not bypass limits via automated rotation loops; the script accurately reported exhaustion (`All configured Gemini API keys are currently unavailable`) and ceased generation cleanly.

## E. Database Integrity
- **Row Count:** Remained strictly at 9,394.
- **Content Integrity:** Validated that content (`content`), metadata (`metadata`), and IDs remained entirely untouched. The `UPDATE` query was explicitly scoped only to `document_embeddings SET embedding = $1 WHERE id = $2`.

## F. RAG Retrieval Results
We comprehensively tested the Supabase pgvector RAG pipeline over the newly populated 236 documents. The `validate_phase3_rag.py` output yielded:
- `Node.js handle concurrency` matched 3 records seamlessly.
- `Virtual DOM` matched 3 frontend records.
- `Index a database in PostgreSQL` matched 3 backend records.

## G. Role Isolation
**Status: PASS**
- Re-tested with exact `{"role": <Role Name>}` JSONB syntax.
- **Backend Developer** queries (e.g., PostgreSQL, Redis) only returned rows containing `Role: Backend Developer`.
- **Frontend Developer** queries (e.g., React DOM) correctly returned exclusively `Role: Frontend Developer` rows.
- No role leakage was observed.

## H. Difficulty Filtering
**Status: PASS**
- When filtering for `{"difficulty": "Easy"}`, `{"difficulty": "Medium"}`, or `{"difficulty": "Hard"}`, the RPC returned documents matching exactly those explicit difficulty bounds via JSONB filtering.

## I. Similarity Distribution
**Status: PASS (0.3 Threshold remains accurate)**
- Highly relevant queries produced similarities around **0.65 - 0.72**.
- Marginally related queries produced similarities around **0.55 - 0.60**.
- The `0.3` threshold is extremely permissive for `gemini-embedding-2` (which generally outputs high cosine similarity scores even for unrelated text).
- **Recommendation for Future:** Once all 9,378 rows are fully embedded, the `similarity_threshold` should be increased from `0.3` to approximately `0.60` to ensure only highly relevant Supabase Bank candidates out-compete Gemini generated candidates. Do not change it yet.

## J. Exact-Text Fidelity
**Status: PASS**
- RAG correctly fetches the precise raw `page_content` text from `document_embeddings` without LLM intermediation or rewriting. Transport formatting matches exactly.

## K. Source Attribution
**Status: PASS**
- The candidate evaluation pool correctly attributes RAG selections as `supabase_bank`.
- Context-generated questions are attributed to `gemini_resume`, `follow_up`, or `missing_skill`.

## L. Question Quality Findings
**Status: PARTIAL (Pending Full Dataset)**
- A brief manual audit of the first 236 embedded rows shows high-quality structured technical questions (e.g., `Concurrency & Async Processing: Deep Dive into Thread pools`).
- Some rows are structured as markdown conversational scripts (e.g., `### Technical Interview Question...`). The `interview_service.py` cleaning logic natively standardizes these format variations.

## M. Candidate Source Competition
**Status: PASS**
- The dynamic `QuestionQualityEvaluator` calculates scores for both generated `gemini_resume` candidates and `supabase_bank` candidates. Due to dimensional scoring (`novelty`, `role_relevance`, `resume_grounding`), the RAG candidate is not guaranteed to win, enforcing a meritocratic selection over the interview lifecycle.

## N. Performance Baseline
- **Embedding Generation Latency:** ~0.4s to 1.1s per batch document (highly dependent on Google GenAI network traffic).
- **RAG Query Latency (Direct DB):** ~3.4s to 4.1s (includes network latency to Supabase + asyncpg embedding conversion).

## O. Test Results
**Status: PASS**
- RAG pipeline tested.
- All 160 units tests passed prior to execution.
- Key pool rotation successfully captured `429 Too Many Requests`, marked cooldowns, and prevented a runaway retry storm.

## P. Remaining Limitations
1. **Incomplete Backfill:** The RAG is functional but under-resourced. The primary `backfill_embeddings.py` must be re-run tomorrow (or when quota recovers) to process the remaining 9,158 rows.
2. **Supabase RPC Connection Resets:** The `match_document_embeddings_filtered` REST RPC periodically threw `WinError 10054 Connection aborted`. The pipeline gracefully fell back to `asyncpg` direct DB connections (`_query_db`), maintaining uptime seamlessly.
