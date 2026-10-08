# Autonomous Implementation Report: PDF Artifacts, Fallback, and Question Generation Fixes

I have successfully completed the autonomous implementation of the final batch of bugs regarding question generation, fallback behavior, and PDF extraction artifacts.

## What Was Fixed

### 1. PDF Extraction Artifact Normalization
- **Issue**: PDF parsing of resumes with icon-fonts (e.g. FontAwesome) resulted in extraction anomalies like `♂laptop-code`, `♂¶usic`, and `/envel⌢pe`. This caused the generated fallback questions to directly hallucinate these artifacts into the text.
- **Fix**: Added `normalize_pdf_artifacts` logic directly to `clean_resume_text` in `app/utils/resume.py`. It specifically targets common icon font ligatures and stray unicode artifacts (`\u2640-\u2642\u00b6\u2322`) while strictly preserving technical terms like `C++` or `.NET`. Also added a fix for missing spaces during bracket concatenation (e.g., `(Nuxt + RAG)Ongoing` -> `(Nuxt + RAG) — Ongoing`).
- **Validation**: Wrote and passed regression tests (`test_pdf_normalization.py`) verifying clean strings on the exact failure cases you documented.

### 2. Gemini API Configuration Order
- **Issue**: `FallbackLLM` was triggering because the `.env` variables were being read before `load_dotenv()` was called in the AI Engine initialization flow, and `key_pool.py` did not correctly split a comma-separated `GEMINI_API_KEY`.
- **Fix**: Re-ordered the dotenv load within `key_pool.py` and implemented graceful fallback handling for comma-separated single keys to ensure live Gemini access works.

### 3. Fallback Question Attribution and Determinism
- **Issue**: When `FallbackLLM` fired or all candidates were rejected, the fallback logic attributed the question to `gemini_resume` instead of `fallback`. Additionally, the fallback target project and technology was completely static (always `0` index), leading to identical first questions when the same resume was uploaded.
- **Fix**: 
  - Changed the fallback candidate attribution source to `"fallback"`.
  - Implemented a `rotation_offset` in `ai_engine/services/interview_service.py` based on an MD5 hash of the `interview_id`. This creates deterministic variety—the first question varies logically across different interview attempts for the same candidate instead of identically defaulting to index `0`.
  - Injected the `interview_id` directly into the `assessment_state` dictionary during interview creation in `app/services/interview_service.py` to allow the AI engine to generate the deterministic offset.
  - Added a final safety hook calling `clean_resume_text` on the final winning `QuestionCandidate` text just before it is sent to the frontend.

### 4. Regression Testing
- Wrote integration scenarios checking extraction cleanliness, fallback rejection tracking, and deterministic session variation in `tests/test_pdf_artifacts_and_fallback.py`. All tests passed cleanly.

I am concluding this autonomous goal session as all immediate repair requirements across the database, Question Bank, Supabase filtering, RAG logic, and interview service generation are now fully completed.
