# InterviewMind AI — Current Project Implementation Audit
**Date:** October 8, 2026  
**Phase:** Phase 5 — Current Project Implementation Audit  
**Mode:** Strictly Read-Only (No application code, database records, or dataset modifications)  
**Corpus State:** 5,000 Canonical Questions Frozen (SHA-256: `0231d302fd970db0e826ac114b820069b763f214fa541d24aba4ebc28c832f87`)

---

## Executive Summary

InterviewMind AI has an established, highly sophisticated end-to-end architecture featuring a FastAPI backend, a React/Vite/TypeScript frontend, a deterministic Resume Processing Module (Module 1), multi-turn adaptive interview orchestration, and an AI Engine backed by Google Gemini and a centralized multi-key failover pool.

The backend test suite is in solid condition with **257 passing tests (0 failures, 0 skipped)** in `backend/tests/`. The frontend builds cleanly with **zero TypeScript errors and zero bundling issues** (`npm run build` completed cleanly in 18.4s).

However, a critical gap exists between the newly completed 5,000-question dataset and the runtime retrieval pipeline:
1. **Supabase Vector Store Incomplete:** Out of 11,886 rows in Supabase `document_embeddings`, 7,664 are marked `inactive` and 4,222 are active. Of the active rows, **only 873 rows have embeddings** (724 for Frontend Developer, 149 for Backend Developer). The remaining 8 roles have `NULL` embeddings in Supabase.
2. **Runtime Question Bank Decoupling:** The runtime question retrieval currently queries Supabase pgvector only; it does not read the local frozen 5,000-question JSONL file (`data/interview_question_bank_v2_generated.jsonl`). Consequently, for 8 out of 10 roles, Supabase pgvector retrieval returns zero candidates.
3. **Resilient Fallback Operating as Intended:** Because the runtime question generator pools multiple sources (Gemini resume-grounded questions, conversational follow-ups, and deterministic category fallbacks), **the live interview flow works smoothly end-to-end even when pgvector returns zero results**, dynamically generating grounded questions from the candidate's resume and live answers.

---

## 1. Backend Architecture

### High-Level Topology

```
                  ┌────────────────────────────────────────┐
                  │          FastAPI (main.py)             │
                  │  Lifespan: init_db(), close_db()       │
                  │  Global Error Handlers & CORS          │
                  └───────────────┬────────────────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         │                                                 │
┌────────▼────────────────┐                     ┌──────────▼──────────────┐
│  /api/health (Health)   │                     │  /api/interview (Core)  │
└─────────────────────────┘                     └──────────┬──────────────┘
                                                           │
                      ┌────────────────────────────────────┼───────────────────────────────────┐
                      │                                    │                                   │
           ┌──────────▼──────────┐              ┌──────────▼──────────┐             ┌──────────▼──────────┐
           │ Resume Processing   │              │ Interview Service   │             │ AI Engine / RAG     │
           │ (Module 1 Service)  │              │ (State & DB Coord)  │             │ Multi-Candidate Gen │
           └──────────┬──────────┘              └──────────┬──────────┘             └──────────┬──────────┘
                      │                                    │                                   │
           ┌──────────▼──────────┐              ┌──────────▼──────────┐             ┌──────────▼──────────┐
           │ Parser / Extractor  │              │ SQLAlchemy Async    │             │ GeminiKeyPool       │
           │ Matcher / Scorer    │              │ Postgres / Supabase │             │ LangChain LLM       │
           └─────────────────────┘              └─────────────────────┘             └─────────────────────┘
```

### Core Components & Data Flow

#### 1. FastAPI Application Entry Point (`backend/main.py`)
- **Input:** HTTP/REST requests on port 8000.
- **Processing:** Configures CORS middleware (`app/core/middleware.py`), initializes asynchronous database connection pools on startup via `lifespan(app: FastAPI)`, disposes connections on shutdown, registers global exception handlers for `BaseInterviewException` (domain errors), `RequestValidationError` (Pydantic 422), `StarletteHTTPException` (HTTP errors), and generic `Exception` (structured 500 JSON).
- **Output:** Structured JSON responses conforming to `{ success: bool, data?: Any, message?: str, error_code?: str }`.

#### 2. Routers (`app/api/routes/`)
- `health.py`: Handles `GET /api/health` providing readiness and dependency status.
- `interview.py`: Handles 11 endpoints spanning the full interview lifecycle: role listing, resume upload, Module 1 resume analysis, interview creation, answer submission, session history, final assessment retrieval, and coding problem submission.

#### 3. Domain & Orchestration Services
- **`InterviewService` (`app/services/interview_service.py`):**
  - **Input:** Request payloads, candidate answers, idempotency keys, session IDs.
  - **Processing:** Owns persisted interview state. Manages database transactions, creates interviews, claims pending questions with SHA-256 fingerprinting to prevent double-submission race conditions, calls `AIProvider` to evaluate answers and generate questions, invokes adaptive state transitions (`app/domain/adaptive.py`), persists transcripts in `interview_messages`.
  - **Output:** Turn response dictionaries containing current evaluation, score, feedback, adaptive difficulty, next question, and session status.
- **`ResumeProcessingService` (`app/resume_processing/service.py`):**
  - **Input:** Resume file bytes or extracted text, target role string, candidate name.
  - **Processing:** Executes 8-step deterministic pipeline:
    1. Parsing (`parser.py` using `pdfplumber` and `docx`)
    2. Extraction (`extractor.py` extracting skills, technologies, experience, projects)
    3. Matching (`matcher.py` against 10 ESCO-aligned roles in `technical_roles.json`)
    4. Deterministic scoring (`scorer.py` computing weighted match score out of 100)
    5. Actionable feedback generation (`feedback.py`)
    6. Module 2 interview context building (`_build_interview_context`)
    7. Qualitative AI analysis (`ai_analyzer.py` via Gemini, attached non-destructively)
    8. Validated output assembly.
  - **Output:** `Module1Output` Pydantic model with `role_match_score`, `score_breakdown`, `matched_areas`, `interview_context`, and `ai_analysis`.

#### 4. Database Layer (`app/core/database.py`, `app/models/`, `app/repositories/`)
- **Engine:** SQLAlchemy 2.0 with `asyncpg` connection pool (pool size: 10, max overflow: 20, pool timeout: 30s).
- **Repositories:** `InterviewRepository` (`app/repositories/interview_repository.py`) isolates all direct database queries for `interviews` and `interview_messages`.

#### 5. Gemini Integration & GeminiKeyPool (`ai_engine/`)
- **Key Pool (`ai_engine/key_pool.py`):** Centralized `GeminiKeyPool` managing multiple API keys configured via `GEMINI_API_KEYS`. Provides thread-safe lock rotation, cooldown tracking (transient rate limit: 60s, daily quota: 86,400s, 503 unavailable/504 timeout: 10s, auth error 401/403: permanent 1-year lockout), and intelligent exception classification.
- **LLM Provider (`ai_engine/models/llm.py`):** Implements `PoolableLLM` wrapping `ChatGoogleGenerativeAI` from `langchain_google_genai` with model `gemini-3.8-flash` (or `gemini-2.5-flash`), temperature=0, and SDK retries disabled to allow `GeminiKeyPool` to manage immediate multi-key failover.
- **Embeddings Provider (`ai_engine/embeddings/embedding_provider.py`):** Uses Google GenAI SDK (`google.genai`) with model `gemini-embedding-2` configured to 1536 output dimensions, operating through `gemini_key_pool.execute_with_fallback`.

#### 6. Semantic Duplicate Detector (`ai_engine/services/semantic_duplicate_detector.py`)
- **Input:** Candidate question text and list of previously asked questions.
- **Processing:** Generates 1536-dimensional embeddings for candidates, calculates cosine similarity against previous question embeddings. If similarity >= 0.82, flags question as duplicate. Falls back gracefully to token n-gram Jaccard overlap if embeddings are unavailable.
- **Output:** Boolean `(is_duplicate, max_similarity, matched_question)`.

---

## 2. Frontend Architecture

### Technology Stack & Entry Points
- **Framework:** React 18 with Vite and TypeScript.
- **Styling & UI:** TailwindCSS, Framer Motion for smooth transitions, Lucide React icons.
- **Entry Points:** `frontend/src/main.tsx` renders `<App />` within `<InterviewProvider>`.
- **Router (`frontend/src/router/index.tsx`):**
  - `/`: `HomePage` (Configuration, role selection, resume upload, Module 1 analysis preview).
  - `/interview`: `InterviewPage` (Active interactive interview room, video/audio gates, questions, voice/text answers, chat history, results).
  - `/404`: `NotFoundPage`.

### User Journey & Component Tree

```
1. HomePage (src/pages/Home/index.tsx)
   ├─ Candidate inputs name & selects Role via JobRoleCombobox
   ├─ Candidate drags & drops / uploads Resume (.pdf / .docx)
   │  └─ POST /api/interview/resume/upload extracts text
   │  └─ POST /api/interview/resume/analyze runs Module 1
   ├─ PreInterviewAnalysisModal (src/components/interview/PreInterviewAnalysisModal.tsx)
   │  └─ Displays Match Score (0-100), Match Breakdown, Verified Strengths, Skill Gaps
   └─ Click "Start Interview"
      └─ POST /api/interview/start creates session & returns Question 1
      └─ Navigates to /interview

2. InterviewPage (src/pages/Interview/index.tsx)
   ├─ MediaReadinessGate: Checks Camera & Microphone access (graceful text fallback)
   ├─ AIInterviewer: Animated interviewer avatar with speaking/listening states
   ├─ QuestionPanel: Renders current question with difficulty badge & TTS Audio
   ├─ ResponsePanel:
   │  ├─ Text Area for typed answer (minimum 10 characters)
   │  ├─ Web Speech API Speech-to-Text (toggle mic for audio recording)
   │  └─ Submit Button (locked during submission to prevent duplicates)
   ├─ Candidate Last Answer display & Collapsible ChatTimeline
   └─ Submit Answer -> POST /api/interview/answer
      └─ Displays live evaluation feedback & loads Question 2...

3. Interview Completion
   └─ If all questions answered OR candidate clicks End Interview:
      └─ Displays PerformanceAnalysis (Overall Score, Technical Breakdown, Communication Score, Recommendation)
```

### State Management (`src/context/InterviewContext.tsx` & `src/hooks/useInterview.ts`)
- Manages `session` state: `interview_id`, `candidateName`, `role`, `topic`, `difficulty`, `currentDifficulty`, `difficultyShift` (`increased`, `decreased`, `unchanged`), `messages` array, `currentEvaluation`, and `startTime`/`endTime`.
- Prevents double submissions using an active `submittingRef` flag and client-side answer length validation.
- Automatically transitions into completion mode when `response.status === 'completed'`.

---

## 3. Current Interview Flow Trace

| Step | Action | Frontend File & Line | API Endpoint | Backend Orchestration | Output to Client |
|---|---|---|---|---|---|
| **1** | User selects role & enters name | `src/pages/Home/index.tsx:54-60` | N/A | Form state validation in React | Validated form state |
| **2** | User uploads resume file | `src/pages/Home/index.tsx:85-130` | `POST /api/interview/resume/upload` | `app/utils/resume.py:extract_text_from_pdf` | Clean resume text & char count |
| **3** | Resume analyzed | `src/pages/Home/index.tsx:62-76` | `POST /api/interview/resume/analyze` | `app/resume_processing/service.py:process` | `Module1Output` with score & gaps |
| **4** | Preview modal viewed & Start clicked | `src/pages/Home/index.tsx:165-184` | `POST /api/interview/start` | `app/services/interview_service.py:58` | `interview_id`, baseline question |
| **5** | Session loaded in UI | `src/pages/Interview/index.tsx:195-236` | N/A | Session rendered; audio synthesized via Web Speech TTS | Question displayed & spoken |
| **6** | Candidate types/speaks answer & clicks submit | `src/pages/Interview/index.tsx:109-130` | `POST /api/interview/answer` | `app/services/interview_service.py:172` | Evaluates answer, adjusts state, generates Q2 |
| **7** | Evaluation displayed & Q2 loaded | `src/hooks/useInterview.ts:145-248` | N/A | Appends evaluation & question to message history | UI updates with score & next question |
| **8** | Consecutive turns continue | Turn loop (steps 6-7) | `POST /api/interview/answer` | Turns increment; adaptive depth & topics shift | Next question or completion |
| **9** | Interview concluded | `src/pages/Interview/index.tsx:136-147` | `POST /api/interview/{id}/end` | `app/services/interview_service.py:471` | Final comprehensive assessment |

---

## 4. Current Question Generation & Multi-Source Competition

### Gemini Model & Invocation Details
- **Model:** `gemini-3.8-flash` (configurable via `GEMINI_MODEL`).
- **Prompt Construction:** Defined in `ai_engine/services/interview_service.py` across four dedicated candidate generators.
- **JSON Parsing (`ai_engine/services/interview_service.py:84`):** `parse_llm_question_json` enforces strict JSON `{ "question": "..." }`, stripping markdown code fences and rejecting conversational preamble.
- **Question Validation (`app/domain/questions.py:validate_question`):** Checks minimum length (>= 20 chars), valid punctuation, absence of conversational meta-commentary, topic/resume relevance, and absence of duplicate wording.

### PRECISE QUESTION GENERATION INVENTORY

| Question Context Dimension | Does Current Runtime Use It? | Code Path & Implementation |
|---|---|---|
| **A. Question Bank Only?** | **No** (competitively pooled) | `ai_engine/services/interview_service.py:824-900` queries Supabase pgvector and enters candidate into `candidate_pool` alongside Gemini candidates. It is never the *only* source. |
| **B. Resume Only?** | **No** (competitively pooled) | `ai_engine/services/interview_service.py:736-822` creates Gemini resume candidate in `resume_phase`, but competes with follow-ups and question bank. |
| **C. Resume + Question Bank?** | **YES** | `ai_engine/services/interview_service.py:656-970` constructs candidate pool including Candidate B (Resume) and Candidate C (Question Bank). |
| **D. Interview History?** | **YES** | `ai_engine/services/interview_service.py:688, 776, 926` passes `previous_questions[-6:]` into prompts with `DO NOT REPEAT` directives; `SemanticDuplicateDetector` rejects duplicates. |
| **E. Current Candidate Answer?** | **YES** | `ai_engine/services/interview_service.py:663-734` uses `last_answer` as primary context for Candidate A (Follow-up), and lines 770-771 as transition context for Candidate B. |
| **F. Role / Difficulty / Strategy?** | **YES** | `ai_engine/services/interview_service.py:679-684` feeds target role, target topic, difficulty definition, rubric, and strategic intent into prompt. |

---

## 5. Current Question Bank Inventory

### Canonical Dataset Audit: `data/interview_question_bank_v2_generated.jsonl`
- **Total Record Count:** Exactly **5,000** records.
- **Role Distribution (10 Roles @ 500 records each):**
  - Backend Developer: 500
  - DevOps / Cloud Engineer: 500
  - Python Developer: 500
  - Frontend Developer: 500
  - Java Developer: 500
  - Database Developer: 500
  - Data Analyst: 500
  - AI Engineer: 500
  - ML Engineer: 500
  - Full Stack Developer: 500
- **Schema Fields (21 fields):** `primary_role`, `role`, `applicable_roles`, `primary_skill`, `skill`, `secondary_skills`, `technology`, `topic`, `category`, `intent`, `difficulty`, `question_type`, `question`, `ideal_answer`, `expected_answer`, `evaluation_rubric`, `id`, `source`, `provenance_type`, `dataset_version`, `status`.
- **Difficulty Breakdown:**
  - `hard` / `Hard`: 1,636 (32.7%)
  - `medium` / `Medium`: 2,363 (47.3%)
  - `easy` / `Easy`: 1,001 (20.0%)
- **Intent Breakdown (13 intents):** `tradeoff` (621), `scenario` (636), `explain` (508), `diagnose` (510), `implement` (483), `concept` (289), `debug` (275), `architecture` (253), `fundamentals` (230), `compare` (149), `optimize` (85), `design` (4), `Assessment` (957).
- **Sources & Provenance:**
  - `Antigravity_Internal_Knowledge` (Phase 4 Gemini generated): 1,838
  - `fallback` (Deterministic taxonomical generation): 1,774
  - `knowledge_base` / Curated / SystemDesign / CodeAlpaca: 1,388
- **Domain Coverage:** 248 unique skills, 114 unique technologies.

### Application Access to Dataset
- **Scripts:** Dataset creation and audit scripts in `backend/scripts/` read and write to this file.
- **Runtime Access:** The application runtime **does not currently read this JSONL directly**. It routes questions exclusively through `ai_engine/vectorstores/supabase_store.py` querying Supabase's `document_embeddings` table.

---

## 6. Current Supabase Database Audit

All queries executed in strictly read-only mode against the live Supabase PostgreSQL instance.

### Tables & Row Counts

| Table Name | Description | Current Row Count | RLS Enabled |
|---|---|---|---|
| `alembic_version` | Migration tracking | 1 | False |
| `code_submissions` | Candidate coding challenge submissions | 0 | True |
| `document_embeddings` | Vector store for question retrieval | **11,886** | True |
| `interview_messages` | Individual Q&A interview turns & evaluations | **278** | True |
| `interviews` | Session metadata, states, profiles, and results | **139** | True |

### Detailed Inspection of `document_embeddings`
- **Total Rows:** 11,886
- **Status Breakdown:**
  - Marked `inactive` (`metadata->>'status' = 'inactive'`): **7,664 rows** (Legacy rows flagged during deduplication/cleanup)
  - Active (`metadata->>'status' != 'inactive'` or NULL): **4,222 rows**
- **Embedding Breakdown among Active Rows:**
  - **Active WITH 1536-dim Embedding:** **873 rows**
    - `Frontend Developer`: 724
    - `Backend Developer`: 149
  - **Active with NULL Embedding:** **3,349 rows** (Python Developer, DevOps, Java Developer, Data Analyst, Database Developer, ML Engineer, AI Engineer, Full Stack Developer)

### Database Schemas, Keys, and Indexes
- **`interviews` Table:**
  - Columns: `id` (UUID PK), `candidate_name` (varchar), `role` (varchar), `topic` (varchar), `difficulty` (varchar), `max_questions` (int), `resume_text` (text), `phase` (varchar), `candidate_profile` (JSON), `role_snapshot` (JSON), `resume_match` (JSON), `assessment_state` (JSON), `final_assessment` (JSON), `coding_result` (JSON), `last_answer_fingerprint` (varchar), `status` (enum: `active`, `completed`, `terminated`), `started_at` (timestamptz), `ended_at` (timestamptz).
  - Indexes: Primary key on `id`, index on `candidate_name`, index on `status`.
- **`interview_messages` Table:**
  - Columns: `id` (UUID PK), `interview_id` (UUID FK -> `interviews.id` ON DELETE CASCADE), `question` (text), `answer` (text), `score` (int), `feedback` (text), `strengths` (text), `improvements` (text), `next_question` (text), `topic` (varchar), `question_difficulty` (varchar), `question_type` (varchar), `technical_concept` (varchar), `technical_evaluation` (JSON), `communication_evaluation` (JSON), `answer_fingerprint` (varchar), `created_at` (timestamptz).
  - Foreign Key: `interview_messages.interview_id` -> `interviews.id`.
- **RPC Vector Search Functions in Supabase:**
  - `match_document_embeddings`: Matches against vector column using cosine distance `<=>`.
  - `match_document_embeddings_filtered`: Accepts `query_embedding`, `match_threshold`, `match_count`, and `metadata_filter` (JSONB containment filter `@>`).

---

## 7. Current RAG Implementation

### Retrieval Flow
1. **Search Query Construction (`ai_engine/services/interview_service.py:845-857`):** Combines `target_technology`, `target_category`, `strategy`, and `difficulty` (e.g. `"react architecture deeper probe hard"`).
2. **Metadata Filtering:** Sets `{"role": mapped_role, "difficulty": difficulty}`.
3. **Embedding Query (`ai_engine/embeddings/embedding_provider.py:20`):** Calls `gemini-embedding-2` with `task_type="RETRIEVAL_QUERY"` producing 1536-dimensional float vector.
4. **Supabase Vector Retrieval (`ai_engine/vectorstores/supabase_store.py:26`):**
   - Calls Supabase REST RPC `/rest/v1/rpc/match_document_embeddings_filtered`.
   - Fallback: Direct asyncpg connection executing `SELECT ... WHERE embedding IS NOT NULL AND metadata @> :filter ORDER BY similarity DESC LIMIT 8`.
5. **Candidate Pool Integration:** Retrieved questions enter `candidate_pool` as `QuestionCandidate(source="supabase_bank", ...)`.
6. **Multi-Candidate Scoring:** Scored alongside Gemini-generated candidates by `QuestionQualityEvaluator`.

### What Works vs What Fails in RAG

| RAG Feature | Status | Explanation |
|---|---|---|
| Query embedding generation | **WORKS** | `EmbeddingProvider` reliably creates 1536-dim vectors via Gemini Key Pool. |
| REST RPC & Direct DB vector query | **WORKS** | Both execution paths work without syntax or network errors. |
| Metadata filtering on role & difficulty | **WORKS** | JSONB `@>` operator correctly filters candidates. |
| Vector retrieval for Frontend / Backend | **WORKS** | 873 active records have embeddings and return matching questions. |
| Vector retrieval for other 8 roles | **FAILS** | 3,349 active records in Supabase have `embedding IS NULL`, so query returns 0 rows. |
| Direct retrieval from local 5,000 JSONL | **NOT IMPLEMENTED** | Runtime does not query `technical_knowledge_5000.jsonl` or `interview_question_bank_v2_generated.jsonl` directly. |

---

## 8. Resume Integration Trace

### Step-by-Step Verification

```
[Resume Upload (.pdf / .docx)]
        │
        ▼
[app/utils/resume.py: extract_text_from_pdf / extract_text_from_file]
        │
        ▼
[app/resume_processing/service.py: ResumeProcessingService.process]
  ├─ Extractor extracts: matched_skills, matched_technologies, matched_projects, matched_experience
  ├─ Matcher computes: role_match_score (0-100), breakdown, missing_skills, evidence
  └─ Output saved in interview.resume_match
        │
        ▼
[ai_engine/services/interview_service.py: generate_question]
  ├─ target_technology = unexplored_techs or matched_technologies
  ├─ target_proj_name = unexplored_projects or matched_projects
  ├─ target_proj_evidence = target_proj_dict["evidence"]
        │
        ▼
[Gemini Resume Prompt Injection (lines 759-800)]
  "CONTEXT:
   - Target Role: {role_name}
   - Target Technology/Topic (PRIMARY CONTEXT): {target_technology}
   - Target Project (PRIMARY CONTEXT): {target_proj_name}
   - Verified Resume Evidence (PRIMARY CONTEXT):
     {evidence_block}
   - Candidate's Last Answer (TRANSITION CONTEXT):
     "{last_answer}""
        │
        ▼
[Gemini Generates Grounded Question]
  e.g.: "In your work with Docker on the Cloud Infrastructure project,
        how did you manage volume persistence during container failovers?"
```

**Verdict:** Resume content **DEFINITELY reaches Gemini during question generation**. It is grounded with extracted evidence, candidate projects, and specific technologies, ensuring the questions are personalized to the candidate's real profile.

---

## 9. Interview Memory Implementation

1. **Storage Layer:**
   - Every question asked is immediately persisted to `interview_messages` with `interview_id`, `topic`, `difficulty`, `question_type`.
   - Candidate answers are stored along with calculated scores, technical evaluations, communication metrics, and idempotency fingerprints.
   - Session metadata in `interviews.assessment_state` tracks `projects_covered`, `technologies_covered`, `categories_covered`, `recent_question_intents`, `weak_areas`, and `misconceptions`.
2. **Consumption in Subsequent Turns:**
   - `previous_questions` is loaded from all messages in the session and fed to:
     - Prompts (`DO NOT REPEAT: ...`)
     - `SemanticDuplicateDetector` (embedding distance checks)
     - `validate_question` (rejection of duplicate turns)
   - `last_answer` is fed directly into Candidate A (Follow-up) and Candidate B (Resume transition).
   - If candidate makes a mistake or reveals a misconception, `adapt_after_answer` flags `misconceptions` in state, triggering a `misconception_diagnostic` follow-up strategy.

---

## 10. API Inventory

| Method | Path | Input Payload | Output Payload | Purpose | Current Status |
|---|---|---|---|---|---|
| `GET` | `/` | None | `{ success, message, version, docs, health }` | Root service descriptor | **READY** |
| `GET` | `/api/health` | None | `{ success, status, services }` | System health check | **READY** |
| `GET` | `/api/interview/roles` | None | `{ roles: [...] }` | List supported roles & skills | **READY** |
| `POST` | `/api/interview/resume/upload` | Multipart form (`file`) | `{ filename, resume_text, char_count }` | PDF/DOCX text extraction | **READY** |
| `POST` | `/api/interview/resume/analyze` | `{ resume_text, role, candidate_name }` | `Module1Output` JSON | Pre-interview match scoring | **READY** |
| `POST` | `/api/interview/start` | `{ candidate_name, role, topic, difficulty, resume_text }` | `{ interview_id, question, role, difficulty, ... }` | Create session & generate Q1 | **READY** |
| `POST` | `/api/interview/answer` | `{ interview_id, answer, idempotency_key? }` | `{ score, feedback, strengths, improvements, next_question, difficulty, status }` | Evaluate answer & generate next Q | **READY** |
| `GET` | `/api/interview/{id}` | Path param `id` (UUID) | `{ interview_id, candidate_name, role, status, ... }` | Fetch session metadata | **READY** |
| `GET` | `/api/interview/{id}/history` | Path param `id` (UUID) | `{ history: [ { question, answer, score, ... } ] }` | Full transcript retrieval | **READY** |
| `POST` | `/api/interview/{id}/end` | Path param `id` (UUID) | `{ interview_id, status: "completed", final_assessment: {...} }` | End session & finalize assessment | **READY** |
| `GET` | `/api/interview/{id}/assessment`| Path param `id` (UUID) | `{ final_assessment: {...} }` | Stored final assessment report | **READY** |
| `GET` | `/api/interview/candidate/{name}/progress` | Path param `name` | `{ candidate_name, total_interviews, assessments: [...] }` | Historical candidate progress | **READY** |
| `POST` | `/api/interview/{id}/coding/problem` | `{ difficulty, language }` | `{ problem_id, title, description, starter_code }` | Role-specific coding problem | **READY** |
| `POST` | `/api/interview/{id}/coding/submit` | `{ problem_id, source_code, language }` | `{ passed, test_results, evaluation }` | Run and review coding submission | **READY** |

---

## 11. Test Status

Execution of backend test suite:
- **Command:** `pytest tests/ -q`
- **Total Tests:** **257**
- **Passing:** **257 (100%)**
- **Failing:** **0**
- **Skipped:** **0**
- **Execution Time:** 51.83 seconds
- **Important Note:** Running `pytest` without specifying `tests/` attempted to run temporary files in `scratch/test_ai_vs_deterministic.py` which had hardcoded relative paths. All canonical tests under `tests/` pass with zero failures.

---

## 12. Demo Readiness Classification

| Feature | Status | Notes |
|---|---|---|
| **Role Selection & Requirements** | **READY** | 10 technical roles configurable via Combobox and API. |
| **Resume Upload (PDF/DOCX)** | **READY** | Fast, robust text extraction with file validation. |
| **Module 1 Resume Match Analysis** | **READY** | Deterministic match score (0-100), breakdown, feedback, and strengths/gaps modal. |
| **Interview Creation & Session State** | **READY** | Stored in PostgreSQL with transaction safety and idempotency. |
| **First Question Generation** | **READY** | Grounded in candidate's verified resume experience. |
| **Candidate Answer Submission** | **READY** | Supports typed text and browser Speech-to-Text; validates length. |
| **Live AI Evaluation & Scoring** | **READY** | Scores (0-10), technical feedback, identified strengths & weaknesses. |
| **Adaptive Next Question & Follow-Up** | **READY** | Adapts difficulty dynamically (Easy -> Medium -> Hard) and probes claims. |
| **Question-Bank RAG Retrieval** | **PARTIALLY READY** | Works for Frontend & Backend roles in Supabase; other 8 roles currently return 0 pgvector rows due to missing embeddings. Resilient fallback to Gemini prevents any failure. |
| **Gemini Multi-Key Failover** | **READY** | Central key pool automatically recovers and rotates across API keys. |
| **Interview History & Transcript** | **READY** | Collapsible timeline in UI; stored in `interview_messages`. |
| **Session Conclusion & Results Page** | **READY** | Comprehensive performance report upon interview end. |
| **Voice Interaction (TTS & STT)** | **READY** | Browser speech synthesis reads questions aloud; microphone captures answers. |

---

## 13. Critical Gaps & Priorities

### P0 (Demo Blockers — Must be aware for today's presentation)
- **Supabase pgvector Missing Embeddings for 8 Roles:**
  - *Symptom:* If demoing Python Developer, DevOps, Java Developer, Data Analyst, Database Developer, ML Engineer, AI Engineer, or Full Stack Developer, Supabase pgvector returns 0 bank questions.
  - *Current Behavior:* The system **does not crash**; Gemini automatically takes over and generates resume-grounded questions.
  - *Demo Action:* For demonstrating Question Bank RAG retrieval specifically, demo with **Frontend Developer** or **Backend Developer** roles, or note that live generation handles the rest.

### P1 (Important Quality & Maintenance Gaps)
- **Local Question Bank Non-Vector Fallback:**
  - `data/interview_question_bank_v2_generated.jsonl` contains 5,000 canonical questions across all 10 roles. Adding a lightweight, non-vector role/topic reader as a RAG fallback would allow all 10 roles to pull from the 5,000 question corpus today without waiting for embeddings.
- **Pytest Root Discovery Configuration:**
  - Add `testpaths = ["tests"]` to `pyproject.toml` or `pytest.ini` so global `pytest` ignores scratch scripts.

### P2 (Post-Demo Improvements)
- Run Phase 6 Embedding Pipeline to vectorize all 5,000 canonical questions with `gemini-embedding-2` and upload to Supabase pgvector.
- Clean up the 7,664 inactive legacy rows in `document_embeddings`.

---

## 14. Target Demo Flow (Shortest Reliable Flow for Today)

The recommended end-to-end demonstration flow that operates with 100% reliability today:

```
Step 1: Open Frontend at http://localhost:5173
Step 2: Enter Candidate Name (e.g., "Alex Chen") and Select Role ("Frontend Developer" or "Backend Developer")
Step 3: Upload Sample Resume (e.g., test_resume.txt or any software engineer PDF)
Step 4: Click "Preview Match Analysis" -> Review Module 1 Match Score & Skill Breakdown Modal
Step 5: Click "Start Interview" -> Audio TTS speaks the personalized first question
Step 6: Speak or type an answer (e.g. explaining system architecture, caching, or React state hooks)
Step 7: Click "Submit Answer" -> Live evaluation appears with score and constructive feedback
Step 8: Observe Adaptive Follow-Up Question probing deeper into the previous answer
Step 9: Answer Turn 2 & Turn 3 to showcase dynamic difficulty adjustment
Step 10: Click "End Interview" -> View comprehensive Performance Analysis report
```

---

## 15. Embeddings Future Plan (Phase 6 Architecture)

For future reference (do NOT execute during Phase 5):
1. **Dataset Source:** `backend/data/knowledge_base/technical_knowledge_5000.jsonl` (Canonical 5,000 frozen questions, SHA-256 confirmed).
2. **Embedding Model:** Google `gemini-embedding-2` via `ai_engine.embeddings.embedding_provider.EmbeddingProvider`.
3. **Dimensions:** 1,536-dimensional vectors with task type `RETRIEVAL_DOCUMENT`.
4. **Target Store:** Supabase PostgreSQL `public.document_embeddings` table with `vector(1536)` column.
5. **Index:** HNSW index on `embedding vector_cosine_ops` for sub-millisecond retrieval.
6. **Query Pipeline:** `SupabaseVectorRetriever` queries `match_document_embeddings_filtered` with cosine similarity >= 0.3, populating Candidate C for all 10 roles.
