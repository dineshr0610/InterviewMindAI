# Implementation Status

- **Phase 1: RAG Candidate Pool Expansion (COMPLETED)**
  - Widened `k` (pool size) to 8.
  - Refactored `interview_service.py` to evaluate each RAG candidate sequentially.
  - Successfully added robust testing to verify fallback logic.
  - Added new `[RAG Diagnostic]` logging fields to candidates.

- **Phase 2: Improve Retrieval Query (COMPLETED)**
  - Refactored `search_query` in `interview_service.py` to concatenate `target_technology`, `target_category`, `strategy`, and `difficulty` rather than a simple 2-word query.

- **Phase 3: Semantic Duplicate Detection (COMPLETED)**
  - Added vector-based semantic repetition checking against previous questions using a temporary 0.85 cosine similarity threshold.
  - Fallback logic triggers correctly on intent mismatch or Gemini API failure.

- **Phase 3.1: Performance Optimization (COMPLETED)**

## Phase 3.1 Performance Report

**1. Embedding API Calls Before vs After**
- **Before**: 1 batch call for `previous_questions` + 1 independent embedding API call for each of the ~8 RAG candidates during evaluation. (Total: **~9 API calls** per interview turn).
- **After**: 1 batch call for `previous_questions` + 1 unified batch call for all candidates in the `candidate_pool` via `prefetch_candidate_embeddings`. (Total: **Exactly 2 API calls** per interview turn).

**2. State of Evaluation Logic**
- **Candidate ordering is fully preserved**: Candidates are still evaluated iteratively by `QuestionQualityEvaluator`.
- **Similarity Calculations remain local**: Cosine similarity is computed securely and locally within `SemanticDuplicateDetector` using NumPy dot products.
- **Evaluation Behavior**: Unchanged. `QuestionQualityEvaluator` still receives identical metrics (similarity score, matching index, semantic threshold flag) and applies identical logic (including intent matching).

**3. Safety & Fallback**
- Empty cases (`previous_questions` or `candidate_pool` empty) are handled safely without generating unnecessary 0-length API requests.
- Failure in the prefetch batch request simply skips semantic duplicate checking for that turn (falling back to Jaccard/Exact match), satisfying the requirement that a batch failure must not crash the interview or spawn 8 isolated retry calls.

**4. Full Test Results**
- The test suite remains entirely green, including the mocked unit tests for semantic duplicates and the 42 main application tests. (**45 / 45 PASSED**).

## Next Steps

- **Phase 4: Question-Bank Cleanup/Validation**
  - Check Supabase records for markdown wrappers, malformed text, etc.
- **Phase 5: Threshold Calibration**
  - Adjust the RAG `0.30` cosine distance threshold using newly collected diagnostic logs.
