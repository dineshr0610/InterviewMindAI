# Adaptive Interview Architecture Summary

## 1. Request Flow

### A. Initialization Flow (`POST /api/interview/start`)
- Validates the role and uses the Module 1 extraction (`parser.py`) to extract resume data.
- Calls `match_resume_to_role` to produce an intersection of Candidate Profile and Role Requirements (ESCO data).
- Initializes the assessment state (`initial_assessment_state`).
- Persists the interview session in the database.
- Immediately calls `_retrieve_question` with `strategy="baseline"`.
- Records the returned question into the database and active state.

### B. Answer Submission Flow (`POST /api/interview/answer`)
- Verifies the answer against idempotency keys and active session limits.
- Evaluates the answer technically (`_evaluate_answer` -> `normalize_technical_evaluation`).
- Evaluates communication style (`analyze_communication`).
- Adapts the state (`adapt_after_answer`), modifying `technical_scores`, `current_difficulty`, `follow_up_depth`, `strong_areas`, `weak_areas`, `misconceptions`, etc.
- Retrieves the next question via `_retrieve_question` using the updated context.
- Updates the message record in the database.

## 2. Question Candidate Generation & Scoring Flow

The central generation and evaluation hub is `generate_question()` within `ai_engine/services/interview_service.py` (which implements `AIInterviewService`).

### Step 1: Context Extraction
The system aggregates:
- `matched_skills`, `matched_technologies`, `matched_projects`
- `missing_skills`
- Historical topics/categories covered
- Candidates' strong/weak areas and misconceptions
- Follow-up depth and difficulty.

### Step 2: Goal/Target Selection
The target category is rotated across predefined Role Categories (e.g., `CAT_ARCHITECTURE`, `CAT_DATA_FLOW`, `CAT_PERFORMANCE`). 
The target project/technology is selected from the available inventory, preferring unexplored elements.

### Step 3: Candidate Generation Sources
The system asynchronously constructs candidates from multiple sources:
- **Candidate A (Follow-up):** Generated if the candidate provided a strong/substantive answer previously and the strategy calls for a follow-up. Prompts Gemini to drill into edge cases and trade-offs.
- **Candidate B (Gemini Resume):** Generated via LLM by grounding heavily in the specific project and technology from the resume, targeting the specified category (e.g., architecture, implementation).
- **Candidate C (Supabase Bank):** Selected from the static, verified Question Bank (via RAG) if it matches the role, difficulty, and technical topic.
- **Candidate D (Missing Skill):** Generated to assess a missing core skill with a hypothetical engineering scenario.

### Step 4: Quality Evaluation (`QuestionQualityEvaluator`)
Every generated candidate passes through a rigorous screening:
1. **Validation Checks:** Imperative structure, length, verbosity.
2. **Duplicate Checks:** Prevents exact matches and semantic duplication (same intent on the same topic).
3. **Hallucination Checks:** Rejects questions asking about non-resume technologies as if they were built by the candidate.
4. **Scoring:** The valid candidates are evaluated on:
    - Role Relevance
    - Resume Relevance & Grounding
    - Answer Continuation Value (diminished by follow-up depth)
    - Novelty
    - Coverage Value
    - Interview Value (base)
    
### Step 5: Selection
Candidates are sorted by total score. The highest-scoring valid candidate is chosen. 
If all candidates fail validation, a deterministic fallback question is provided (this fallback lacked dimensional scores, which caused the "0.0 breakdown" issue identified in logs).

## Planned Improvements for Phase 2:
1. Fix the 0.0 scoring logs (assign baseline dimensional scores to the fallback).
2. Deepen the `adapt_after_answer` logic to pass precise, state-driven intents to the candidate generation pool (e.g., explicitly demanding a misconception-targeted question if a misconception was identified).
3. Refine `generate_question` candidate rules to support diversity.
4. Ensure historical question/intent passing prevents redundant probing.
