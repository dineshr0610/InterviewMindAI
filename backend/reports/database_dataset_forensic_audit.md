# Phase 0: Complete Database & Dataset Forensic Audit Report
**InterviewMind AI — Backend & Vector Database Audit**

> **CRITICAL SAFETY DIRECTIVE COMPLIANCE:** This audit was conducted entirely in **READ-ONLY** mode. Zero database mutations (INSERT/UPDATE/DELETE/ALTER), zero embedding regenerations, and **0 Gemini API calls** were made.

## Executive Summary
This forensic audit investigated the real Supabase PostgreSQL database, its underlying dataset (`document_embeddings`), relational tables (`interviews`, `interview_messages`, `code_submissions`, `alembic_version`), and application integration layers.

### High-Impact Forensic Findings:
1. **The 689 'Normalized Questions' are 100% Synthetic Boilerplate:** All 689 questions extracted during Phase 4.1/4.2 originate from a single synthetic generator script (`dataset_generator.py`) and share an identical sentence template: *'Explain how {subtopic} operates in the context of {topic}... What are the primary trade-offs...'* Many suffer from string-splitting defects resulting in corrupted syntax (e.g., `List (ArrayList`, `LinkedList)`). **Embedding these 689 rows would waste API quota on synthetic artifacts rather than real interview questions.**
2. **Real Interview Questions Were Excluded:** Authentic interview questions from GitHub repositories (e.g., `javascript-interview-questions`, `reactjs-interview-questions`, `system-design-primer`, `devops-exercises`) were either quarantined as tutorials or left unextracted because extraction heuristics strictly looked for `**Question**:` markers that only existed in synthetic templates.
3. **Critical RAG Role Filter Bug in Code:** In `document_embeddings`, the role metadata stores Title Case values (e.g. `'Backend Developer'`) in the `role` field, while snake_case (e.g. `'backend_developer'`) is stored in `role_id`. However, `InterviewService` creates filters as `{'role': 'backend_developer'}`. Because PostgreSQL JSONB containment `@>` requires exact string matching, **RAG role-filtered queries return 0 results**.
4. **Unscientific Difficulty Assignment:** Difficulty labels in the dataset are not human-calibrated. In scraped data, difficulty was assigned purely on character length (>800 chars = 'Hard'). In synthetic data, difficulty was cycled round-robin (`i % 3`), creating 129 identical duplicate question groups labeled simultaneously as Easy, Medium, and Hard.
5. **Missing Taxonomy Fields:** There are **zero** `skill`, `technology`, `intent`, or `strategy` fields in `document_embeddings.metadata`. The `subtopic` field is severely corrupted (containing 6,571 distinct values, mostly raw markdown headers like `## Answer: 1`).

---

## Part 1 — Database Schema Inventory
The database currently contains 5 public tables and 3 vector search RPC functions.

### Table: `public.alembic_version`
- **Row Count:** 1
- **Primary Key:** `version_num`
- **RLS Enabled:** `True` | **RLS Forced:** `False`
- **RLS Policies:** 0 defined (No policies exist; table relies on database superuser / service_role bypass)

**Columns:**
| Column | Data Type (UDT) | Nullable | Default |
|---|---|---|---|
| `version_num` | `character varying` (`varchar`) | `NO` | `None` |

**Indexes:**
- `alembic_version_pkc`: `CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num)`


### Table: `public.code_submissions`
- **Row Count:** 0
- **Primary Key:** `id`
- **RLS Enabled:** `True` | **RLS Forced:** `False`
- **RLS Policies:** 0 defined (No policies exist; table relies on database superuser / service_role bypass)

**Columns:**
| Column | Data Type (UDT) | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` (`uuid`) | `NO` | `None` |
| `interview_id` | `uuid` (`uuid`) | `NO` | `None` |
| `problem_id` | `character varying` (`varchar`) | `NO` | `None` |
| `language` | `character varying` (`varchar`) | `NO` | `None` |
| `source_code` | `text` (`text`) | `NO` | `None` |
| `result` | `json` (`json`) | `YES` | `None` |
| `created_at` | `timestamp with time zone` (`timestamptz`) | `NO` | `now()` |

**Foreign Keys:**
- `interview_id` &rarr; `public.interviews(id)` (ON DELETE: `CASCADE`, ON UPDATE: `NO ACTION`)

**Indexes:**
- `code_submissions_pkey`: `CREATE UNIQUE INDEX code_submissions_pkey ON public.code_submissions USING btree (id)`
- `ix_code_submissions_id`: `CREATE INDEX ix_code_submissions_id ON public.code_submissions USING btree (id)`
- `ix_code_submissions_interview_id`: `CREATE INDEX ix_code_submissions_interview_id ON public.code_submissions USING btree (interview_id)`


### Table: `public.document_embeddings`
- **Row Count:** 9394
- **Primary Key:** `id`
- **RLS Enabled:** `True` | **RLS Forced:** `False`
- **RLS Policies:** 0 defined (No policies exist; table relies on database superuser / service_role bypass)

**Columns:**
| Column | Data Type (UDT) | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` (`uuid`) | `NO` | `gen_random_uuid()` |
| `content` | `text` (`text`) | `NO` | `None` |
| `metadata` | `jsonb` (`jsonb`) | `YES` | `'{}'::jsonb` |
| `embedding` | `USER-DEFINED` (`vector`) | `YES` | `None` |
| `created_at` | `timestamp with time zone` (`timestamptz`) | `YES` | `now()` |

**Indexes:**
- `document_embeddings_pkey`: `CREATE UNIQUE INDEX document_embeddings_pkey ON public.document_embeddings USING btree (id)`
- `document_embeddings_vector_idx`: `CREATE INDEX document_embeddings_vector_idx ON public.document_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists='100')`
- `document_embeddings_metadata_idx`: `CREATE INDEX document_embeddings_metadata_idx ON public.document_embeddings USING gin (metadata)`


### Table: `public.interview_messages`
- **Row Count:** 278
- **Primary Key:** `id`
- **RLS Enabled:** `True` | **RLS Forced:** `False`
- **RLS Policies:** 0 defined (No policies exist; table relies on database superuser / service_role bypass)

**Columns:**
| Column | Data Type (UDT) | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` (`uuid`) | `NO` | `None` |
| `interview_id` | `uuid` (`uuid`) | `NO` | `None` |
| `question` | `text` (`text`) | `NO` | `None` |
| `answer` | `text` (`text`) | `YES` | `None` |
| `score` | `integer` (`int4`) | `YES` | `None` |
| `feedback` | `text` (`text`) | `YES` | `None` |
| `strengths` | `text` (`text`) | `YES` | `None` |
| `improvements` | `text` (`text`) | `YES` | `None` |
| `next_question` | `text` (`text`) | `YES` | `None` |
| `created_at` | `timestamp with time zone` (`timestamptz`) | `NO` | `now()` |
| `topic` | `character varying` (`varchar`) | `YES` | `None` |
| `question_difficulty` | `character varying` (`varchar`) | `YES` | `None` |
| `question_type` | `character varying` (`varchar`) | `YES` | `None` |
| `technical_concept` | `character varying` (`varchar`) | `YES` | `None` |
| `technical_evaluation` | `json` (`json`) | `YES` | `None` |
| `communication_evaluation` | `json` (`json`) | `YES` | `None` |
| `answer_fingerprint` | `character varying` (`varchar`) | `YES` | `None` |

**Foreign Keys:**
- `interview_id` &rarr; `public.interviews(id)` (ON DELETE: `CASCADE`, ON UPDATE: `NO ACTION`)

**Indexes:**
- `interview_messages_pkey`: `CREATE UNIQUE INDEX interview_messages_pkey ON public.interview_messages USING btree (id)`
- `ix_interview_messages_id`: `CREATE INDEX ix_interview_messages_id ON public.interview_messages USING btree (id)`
- `ix_interview_messages_interview_id`: `CREATE INDEX ix_interview_messages_interview_id ON public.interview_messages USING btree (interview_id)`


### Table: `public.interviews`
- **Row Count:** 139
- **Primary Key:** `id`
- **RLS Enabled:** `True` | **RLS Forced:** `False`
- **RLS Policies:** 0 defined (No policies exist; table relies on database superuser / service_role bypass)

**Columns:**
| Column | Data Type (UDT) | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` (`uuid`) | `NO` | `None` |
| `candidate_name` | `character varying` (`varchar`) | `NO` | `None` |
| `role` | `character varying` (`varchar`) | `NO` | `None` |
| `topic` | `character varying` (`varchar`) | `NO` | `None` |
| `difficulty` | `character varying` (`varchar`) | `NO` | `'Easy'::character varying` |
| `status` | `USER-DEFINED` (`interview_status`) | `NO` | `'ACTIVE'::interview_status` |
| `started_at` | `timestamp with time zone` (`timestamptz`) | `NO` | `now()` |
| `ended_at` | `timestamp with time zone` (`timestamptz`) | `YES` | `None` |
| `max_questions` | `integer` (`int4`) | `NO` | `50` |
| `resume_text` | `text` (`text`) | `YES` | `None` |
| `current_topic` | `character varying` (`varchar`) | `YES` | `None` |
| `covered_topics` | `json` (`json`) | `YES` | `None` |
| `phase` | `character varying` (`varchar`) | `NO` | `'technical'::character varying` |
| `candidate_profile` | `json` (`json`) | `YES` | `None` |
| `role_snapshot` | `json` (`json`) | `YES` | `None` |
| `resume_match` | `json` (`json`) | `YES` | `None` |
| `assessment_state` | `json` (`json`) | `YES` | `None` |
| `final_assessment` | `json` (`json`) | `YES` | `None` |
| `coding_result` | `json` (`json`) | `YES` | `None` |
| `last_answer_fingerprint` | `character varying` (`varchar`) | `YES` | `None` |

**Indexes:**
- `interviews_pkey`: `CREATE UNIQUE INDEX interviews_pkey ON public.interviews USING btree (id)`
- `ix_interviews_id`: `CREATE INDEX ix_interviews_id ON public.interviews USING btree (id)`
- `ix_interviews_candidate_name`: `CREATE INDEX ix_interviews_candidate_name ON public.interviews USING btree (candidate_name)`
- `ix_interviews_status`: `CREATE INDEX ix_interviews_status ON public.interviews USING btree (status)`


### Database RPC Functions (Vector Search)
#### Function: `test_document_similarity`
```sql
CREATE OR REPLACE FUNCTION public.test_document_similarity(query_embedding vector)
 RETURNS TABLE(content text, similarity double precision)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
    SELECT
        de.content,
        (1 - (de.embedding <=> query_embedding))::double precision
    FROM public.document_embeddings de
    WHERE de.embedding IS NOT NULL
    ORDER BY de.embedding <=> query_embedding
    LIMIT 5;
$function$

```

#### Function: `match_document_embeddings`
```sql
CREATE OR REPLACE FUNCTION public.match_document_embeddings(query_embedding vector, match_threshold double precision DEFAULT 0.0, match_count integer DEFAULT 5)
 RETURNS TABLE(id uuid, content text, metadata jsonb, similarity double precision)
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
            BEGIN
                RETURN QUERY
                SELECT
                    de.id,
                    de.content,
                    de.metadata,
                    (1 - (de.embedding <=> query_embedding))::double precision AS sim
                FROM public.document_embeddings AS de
                WHERE de.embedding IS NOT NULL
                  AND (1 - (de.embedding <=> query_embedding)) >= match_threshold
                ORDER BY sim DESC
                LIMIT match_count;
            END;
            $function$

```

#### Function: `match_document_embeddings_filtered`
```sql
CREATE OR REPLACE FUNCTION public.match_document_embeddings_filtered(query_embedding vector, metadata_filter jsonb DEFAULT '{}'::jsonb, match_threshold double precision DEFAULT 0.3, match_count integer DEFAULT 2)
 RETURNS TABLE(id uuid, content text, metadata jsonb, similarity double precision)
 LANGUAGE sql
 STABLE
AS $function$
            SELECT de.id, de.content, de.metadata, 1 - (de.embedding <=> query_embedding) AS similarity
            FROM document_embeddings de
            WHERE de.embedding IS NOT NULL
              AND de.metadata @> metadata_filter
              AND (de.metadata->>'status' IS NULL OR de.metadata->>'status' != 'inactive')
              AND 1 - (de.embedding <=> query_embedding) >= match_threshold
            ORDER BY de.embedding <=> query_embedding
            LIMIT match_count;
        $function$

```

## Part 2 — Relationship Map
### Formal Relational Constraints (PostgreSQL FKs)
```mermaid
graph TD
    interviews -->|1:N (CASCADE)| interview_messages
    interviews -->|1:N (CASCADE)| code_submissions
    alembic_version[alembic_version (Isolated)]
    document_embeddings[document_embeddings (Isolated Vector Store)]
```

### Architectural Connection Analysis
1. **Core Relational Core:** `interviews` acts as the root entity. Both `interview_messages` and `code_submissions` have explicit foreign keys to `interviews.id` with `ON DELETE CASCADE`.
2. **`alembic_version`:** Independent migration tracking table managed by SQLAlchemy/Alembic. Currently recorded at migration `004_assessment_extensions`.
3. **`document_embeddings` is NOT formally related:** `document_embeddings` has **ZERO** foreign key constraints linking to `interviews` or any other table. It is NOT managed by Alembic migrations (it was initialized via standalone SQL script `alembic/pgvector_setup.sql`).
4. **Application-Level Coupling:** The connection between `document_embeddings` and `interview_messages` exists exclusively in application memory:
   - At runtime, `InterviewService.generate_question()` calls `RAGService.ask()`.
   - `RAGService` retrieves rows from `document_embeddings` via `SupabaseVectorRetriever`.
   - If selected by `QuestionQualityEvaluator`, the question string is populated in a `QuestionCandidate` and subsequently written into `interview_messages.question` upon saving the turn.

---

## Part 3 — document_embeddings Forensic Audit
- **Total Rows in Dataset:** 9,394
- **Populated Embeddings:** 4,630 (49.3%)
- **NULL Embeddings:** 4,764 (50.7%)
- **Active Records:** 0 (0%)
- **Inactive / Quarantined Records:** 7,664 (81.6%)
- **Unspecified Status Records:** 1,730 (18.4%)

### Question Data Quality Classification (Heuristic Audit)
| Classification Category | Row Count | Percentage | Description |
|---|---|---|---|
| **QUESTION + RUBRIC** | 4,174 | 44.4% | Records containing explicit evaluation criteria, scoring, or candidate rubrics. |
| **EXPLANATION WITHOUT QUESTION** | 2,423 | 25.8% | Theoretical explanations, notes, or concept deep-dives without an actual question. |
| **CODE EXAMPLE WITHOUT QUESTION** | 847 | 9.0% | Stand-alone code snippets or syntax demonstrations lacking an interview prompt. |
| **CLEAN QUESTION** | 686 | 7.3% | Short, standalone questions ending with '?' without markdown fences or answers. |
| **FULL TUTORIAL/ARTICLE** | 676 | 7.2% | Comprehensive articles or documentation chapters exceeding 250 words. |
| **QUESTION WITH METADATA** | 364 | 3.9% | Questions that include contextual headings or brief intro notes. |
| **UNKNOWN** | 143 | 1.5% | Records with unstructured or mixed syntax patterns. |
| **QUESTION + ANSWER** | 81 | 0.9% | Records that explicitly bundle the question and the model answer/solution. |

> **Forensic Reality:** Less than 7.5% of the database represents clean, standalone interview questions. Over 92% of the dataset consists of model answers, rubrics, full tutorials, and explanatory documentation.

---

## Part 4 — Actual Dataset Schema (Metadata Fields)
| Field Name | Present Count | Null Rate | Distinct Values | Sample Values / Description | Quality Problems |
|---|---|---|---|---|---|
| `question` | 0 | 100.0% | 0 | None | Field completely missing from metadata. |
| `skill` | 0 | 100.0% | 0 | None | Field completely missing from metadata. |
| `technology` | 0 | 100.0% | 0 | None | Field completely missing from metadata. |
| `topic` | 9,394 | 0.0% | 137 | 'Python Algorithms & Data Structures', 'JavaScript / DOM / React Tasks', 'JavaScript Core & DOM' | None |
| `subtopic` | 9,388 | 0.1% | 6,571 | '## Answer: 1', '## Answer: 4', '## Answer: 2' | Severe markdown pollution (headers like '## Answer: 1'). |
| `category` | 9,393 | 0.0% | 7 | 'Coding', 'Theory', 'Data Structures & Algorithms' | Virtually binary ('Coding' vs 'Theory') despite 10 code categories. |
| `role` | 9,388 | 0.1% | 10 | 'Python Developer', 'Frontend Developer', 'Java Developer' | Title Case ('Backend Developer') conflicts with snake_case code filter. |
| `role_id` | 9,388 | 0.1% | 10 | 'python_developer', 'frontend_developer', 'java_developer' | None |
| `difficulty` | 9,388 | 0.1% | 3 | 'Easy', 'Hard', 'Medium' | Assigned via character length or round-robin loop. |
| `strategy` | 0 | 100.0% | 0 | None | Field completely missing from metadata. |
| `intent` | 0 | 100.0% | 0 | None | Field completely missing from metadata. |
| `answer` | 0 | 100.0% | 0 | None | Field completely missing from metadata. |
| `explanation` | 0 | 100.0% | 0 | None | Field completely missing from metadata. |
| `rubric` | 0 | 100.0% | 0 | None | Field completely missing from metadata. |
| `evaluation_rubric` | 0 | 100.0% | 0 | None | Field completely missing from metadata. |
| `tags` | 0 | 100.0% | 0 | None | Field completely missing from metadata. |
| `source` | 9,388 | 0.1% | 10 | 'https://github.com/sahil280114/codealpaca', 'InterviewMind-AI-Curated-Dataset-v1', 'https://raw.githubusercontent.com/sudheerj/javascript-interview-questions/master/README.md' | None |
| `metadata` | 0 | 100.0% | 0 | None | Field completely missing from metadata. |
| `status` | 7,664 | 18.4% | 1 | 'inactive' | None |
| `languages` | 3,261 | 65.3% | 9 | 'list:Python', 'list:JavaScript,TypeScript,HTML', 'list:Java' | None |
| `dataset_type` | 6,127 | 34.8% | 2 | 'Real-World-CodeAlpaca-20k', 'Real-World-Curated-Online' | None |

---

## Part 5 — Skill Analysis
- **Total Distinct Topics:** 137 (100 in primary curated set)
- **Is there a `skill` field?** **NO.** There is no field named `skill` or `technology` in metadata.

### Distribution & Concept Analysis:
1. **Compound Multi-Concept Fields:** Instead of atomic skills (e.g. `'Python'`, `'SQL'`, `'React'`), `topic` values combine technology, exercise type, and discipline:
   - `'Python Algorithms & Data Structures'` (2,272 rows)
   - `'JavaScript / DOM / React Tasks'` (754 rows)
   - `'Bash & Automation Scripts'` (86 rows)
   - `'SQL Queries & Schema Design'` (457 rows)
2. **Duplicate & Overlapping Concepts:** Multiple topics refer to the same domain with differing granularity:
   - `'JavaScript / DOM / React Tasks'` (754) vs `'JavaScript Core & DOM'` (716) vs `'JavaScript Core & ES6+'` (44)
   - `'React & Hooks'` (581) vs `'React Component Tasks'` (47)
   - `'SQL Queries & Schema Design'` (457) vs `'SQL Analytical Queries'` (15) vs `'Data Analytics & SQL Queries'` (74)
   - `'Cloud Computing & AWS'` (61) vs `'Cloud Computing Fundamentals (AWS/Azure/GCP)'` (44)
3. **Massive Representation Imbalance:**
   - A single topic (`'Python Algorithms & Data Structures'`) accounts for **24.2%** of the entire database.
   - Meanwhile, 38 specialized topics contain exactly 15 records each, and crucial disciplines like CI/CD contain only 5 records.

---

## Part 6 — Question Quality Analysis
### Global Text Syntax Metrics:
- **Questions ending with '?':** 690 (7.3%)
- **Records containing '?' elsewhere:** 1,159 (17.3%)
- **Records with NO '?' anywhere:** 7,545 (75.4%)
- **Records with Markdown Code Fences (` ``` `):** 5,865 (62.4%)
- **Records with Markdown Headings (`#`, `##`, `###`):** 8,699 (92.6%)
- **Records with Model Answer Markers:** 88
- **Records with Rubric Markers:** 4,509
- **Records over 1,000 characters:** 1,976

### Concrete Examples of Problem Categories in the Database:

#### 1. Non-Question Explanation (Missing '?')
> **ID:** `6d734390-b218-44ea-b3fc-28b24a54129e` | **Topic:** `Binary Search`  
> *"Binary Search requires sorted data and repeatedly divides the search space in half."*

#### 2. Synthetic Template Boilerplate
> **ID:** `8d6663fe-ebd1-4b73-b476-39aec8bd1c10` | **Topic:** `DSA & Problem Solving`  
> *"Explain how Dijkstra shortest path operates in the context of DSA & Problem Solving. What are the primary trade-offs when choosing this approach over standard alternatives in Java Developer applications?"*

#### 3. Full Document Bundling Question + Answer
> **ID:** `2934c627-8079-4230-a012-f2de8a71022b` | **Topic:** `JavaScript Core & DOM`  
> *"### Technical Interview Question: Why do I need to use the freeze method

**Role**: Frontend Developer | **Topic**: JavaScript Core & DOM | **Difficulty**: Easy

#### Technical Explanation & Model Answer
In the Object-oriented paradigm, an existing API contains certain elements that are not intended"*

#### 4. Code Generation Instruction Prompt (CodeAlpaca style)
> **ID:** `29e048ab-56aa-44e2-8e7d-aaf3cdc88196` | **Topic:** `Python Algorithms & Data Structures`  
> *"### Real Coding Task: Write a Python program to implement a text-based game

**Role**: Python Developer | **Category**: Coding | **Difficulty**: Hard

#### Problem Description
Write a Python program to implement a text-based game

#### Verified Solution & Code Implementation
```text
import random

d"*

#### 5. Fake Production Scenario Template
> **ID:** `b5010667-5392-4956-b250-1d06b9675f56` | **Topic:** `CSS3 & Modern Styling`  
> *"### Production Scenario: Scaling CSS3 & Modern Styling with Specificity

**Role**: Frontend Developer | **Difficulty**: Medium

#### Problem Statement
A high-concurrency production service for a Frontend Developer application encounters performance bottlenecks and latency spikes during peak load. Th"*

---

## Part 7 — Difficulty Analysis
| Difficulty Level | Record Count | Percentage |
|---|---|---|
| **Hard** | 3,677 | 39.1% |
| **Easy** | 3,818 | 40.6% |
| **Medium** | 1,893 | 20.2% |
| **NULL / Missing** | 6 | 0.1% |

### Forensic Findings on Difficulty Reliability:
1. **Not Pedagogically Valid:** The difficulty values in the database are completely untrustworthy.
2. **Length-Based Assignment:** In `download_and_clean_real_dataset.py`, difficulty was assigned purely on text length:
   ```python
   if len(body_clean) > 800 or '```' in body_clean: difficulty = 'Hard'
   elif len(body_clean) > 350: difficulty = 'Medium'
   else: difficulty = 'Easy'
   ```
   This means a simple concept with a verbose explanation was labeled 'Hard', while an intrinsically difficult concept explained concisely was labeled 'Easy'.
3. **Round-Robin Modulo Assignment:** In `dataset_generator.py`, synthetic entries cycled `['Easy', 'Medium', 'Hard'][i % 3]`. This produced identical questions labeled as 'Easy', 'Medium', and 'Hard' across different rows.

---

## Part 8 — Role Analysis
| Role Title | Record Count | `role_id` Equivalent |
|---|---|---|
| **Python Developer** | 2,583 | `python_developer` |
| **Frontend Developer** | 2,470 | `frontend_developer` |
| **Java Developer** | 920 | `java_developer` |
| **Database Developer** | 735 | `database_developer` |
| **DevOps / Cloud Engineer** | 625 | `devops__cloud_engineer` |
| **Backend Developer** | 571 | `backend_developer` |
| **Data Analyst** | 397 | `data_analyst` |
| **AI Engineer** | 385 | `ai_engineer` |
| **Machine Learning Engineer** | 374 | `machine_learning_engineer` |
| **Full Stack Developer** | 328 | `full_stack_developer` |

### Critical Bug: Role Metadata Mismatch
- In database metadata, the `role` key stores Title Case strings (e.g. `'Backend Developer'`), and the `role_id` key stores snake_case strings (e.g. `'backend_developer'`).
- In application code (`interview_service.py`), the RAG filter is constructed as:
  ```python
  mapped_role = role_name.strip().lower().replace(' ', '_').replace('-', '_')
  filters['role'] = mapped_role  # e.g. 'backend_developer'
  ```
- This submits `metadata @> '{"role": "backend_developer"}'` to Supabase PostgreSQL.
- **Result:** ZERO records match. Whenever `filters['role']` was applied, RAG silently returned empty results and fell through to Gemini generation.

---

## Part 9 — Category / Intent / Strategy Analysis
### In the Database:
- **Category:** Only two categories dominate: `'Coding'` (5,313 records, 56.6%) and `'Theory'` (4,075 records, 43.4%), with 5 scattered legacy records.
- **Intent:** `0` records possess an `intent` field.
- **Strategy:** `0` records possess a `strategy` field.

### In Application Code (`interview_service.py` & `QuestionQualityEvaluator`):
- The application defines a rich 10-category taxonomy: `architecture`, `data_flow`, `implementation`, `technology_choice`, `database_design`, `api_design`, `security`, `debugging_profiling`, `tradeoff_analysis`, `role_competency`.
- The application also models pedagogical intents: `explain`, `tradeoff`, `debug`, `design`, `deepen`, `validate`.
- **Disconnection:** Because none of these exist in `document_embeddings`, the vector database cannot participate in category rotation or intent-driven question selection.

---

## Part 10 — Embedding Audit
- **Vector Dimensions:** 1536
- **Populated Embeddings:** 4,630
- **NULL Embeddings:** 4,764
- **Embedding Model:** `gemini-embedding-2` (not tracked in database metadata)

### Key Forensic Finding:
- The 4,630 existing non-null embeddings were computed over the **entire raw document text** (`content`), including markdown headers, model answers, code snippets, and evaluation rubrics.
- They do NOT represent the semantic vector of an interview question.
- When searching for question semantics (e.g. *'How does garbage collection work in Python?'*), the vector compares against the embedding of an entire multi-section document, degrading cosine similarity precision.
- **Existing embeddings cannot be reused** once questions are normalized.

---

## Part 11 — Duplicate Analysis
- **Exact Duplicate Groups:** 129
- **Affected Records in Duplicate Groups:** 317
- **Groups Differing Only in Difficulty:** 129 (100% of duplicate groups!)
- **Groups Differing in Role:** 0
- **Groups Differing in Topic:** 0

### Forensic Significance:
Every single duplicate group in the dataset is an artifact of the synthetic generator's round-robin difficulty loop. The exact same question text was generated three times and labeled 'Easy', 'Medium', and 'Hard'.
Example duplicate triad:
```
Question: 'Explain how Linked list cycle detection operates in the context of DSA & Problem Solving. What are the primary trade-offs when choosing this approach...'
  - Row 1 (e2b7dcec): Difficulty = 'Easy'
  - Row 2 (464abf7d): Difficulty = 'Medium'
  - Row 3 (44d76be5): Difficulty = 'Hard'
```

## Part 12 — Other Tables Audit
### 1. `public.interviews` (139 rows)
- Tracks candidate sessions. Active interviews: 95, Completed: 44.
- Roles exhibit case/naming inconsistency: `'Backend Developer'` (23), `'Frontend developer'` (16), `'SOFTWARE ENGINEER'` (15), `'Software Developer'` (13).
- Topic column contains unnormalized strings, including full role descriptions (e.g. `'Frontend Developer: JavaScript, TypeScript, React, HTML, CSS, browser fundamentals, REST APIs...'`).

### 2. `public.interview_messages` (278 rows)
- 238 out of 278 rows (85.6%) have NULL `question_type` and NULL `question_difficulty`.
- **Prompt Leakage Artifacts:** Past questions stored in `interview_messages` show severe prompt leakage:
  > *"Can you explain the core principles of Generate one Easy level interview question on Python. Return only JSON. ?"*

### 3. `public.code_submissions` (0 rows)
- Schema exists (`interview_id`, `problem_id`, `language`, `source_code`, `result`), currently unpopulated.

---

## Part 13 — Application &harr; Database Mapping
### Data Flow Analysis:
1. **Write Path:** `document_embeddings` is populated via offline batch scripts (`ingest.py`, `ingest_bulk.py`). It is NOT written during live interview turns.
2. **Read Path:** `interview_service.py` calls `RAGService.ask()` -> `SupabaseVectorRetriever` -> PostgREST RPC `match_document_embeddings_filtered` -> `public.document_embeddings`.
3. **Mismatch Point 1 (Role Filter):** Code passes `filters['role'] = snake_case`, but DB stores Title Case in `role` and snake_case in `role_id`.
4. **Mismatch Point 2 (Content Expectations):** Code expects `doc.page_content` to be a concise question. In reality, it receives multi-paragraph markdown documents.
5. **Mismatch Point 3 (Fallback Dependency):** Because RAG queries often failed due to the role filter bug or returned unparseable multi-paragraph tutorials rejected by `QuestionQualityEvaluator`, the system continually fell through to Gemini generation.

---

## Part 14 — Ideal Dataset Contract
To establish a robust question bank for InterviewMind AI, each canonical question record should adhere to the following schema:

```json
{
  "id": "uuid (Primary Key)",
  "question": "string (Clean, concise, standalone question ending with '?')",
  "role_id": "string (Canonical snake_case: 'backend_developer', 'frontend_developer', etc.)",
  "primary_skill": "string (Canonical skill: 'Python', 'React', 'PostgreSQL', 'Docker')",
  "secondary_skills": ["string (Optional associated skills)"],
  "category": "string (Canonical category: 'architecture', 'implementation', 'debugging', etc.)",
  "intent": "string (Canonical intent: 'explain', 'tradeoff', 'debug', 'design')",
  "difficulty": "string ('Easy' | 'Medium' | 'Hard' - verified by technical rubrics)",
  "expected_answer": "string (Concise model answer or key evaluation points)",
  "evaluation_rubric": {
    "strong_indicators": ["string"],
    "weak_indicators": ["string"]
  },
  "source": "string (Dataset origin or benchmark reference)",
  "status": "string ('active' | 'draft' | 'deprecated')",
  "embedding": "vector(1536) (Computed strictly over the question text)",
  "created_at": "timestamptz",
  "updated_at": "timestamptz"
}
```

### Contract Division:
- **REQUIRED:** `id`, `question`, `role_id`, `primary_skill`, `difficulty`, `category`, `intent`, `status`.
- **OPTIONAL:** `secondary_skills`, `expected_answer`, `evaluation_rubric`, `source`.
- **DERIVED:** `embedding` (generated from `question`), `token_count`, timestamps.
- **NOT NEEDED / PROHIBITED:** Multi-paragraph tutorial markdown blocks, synthetic boilerplate templates, pseudo-code demos.

---

## Part 15 — Dataset Problems vs. Code Problems
### DATASET PROBLEMS (Must be fixed in the data):
1. **Data Pollution:** 92.5% of `document_embeddings` rows contain tutorials, rubrics, and model answers rather than questions.
2. **Synthetic Template Monotony:** The 689 normalized rows are 100% identical synthetic sentences with broken string splits (e.g. `List (ArrayList`).
3. **Missing Canonical Skills:** Metadata lacks `skill` and `technology` fields entirely.
4. **Corrupted Subtopics:** 6,571 subtopic values contaminated by markdown heading fragments.
5. **Arbitrary Difficulty Labels:** Difficulty assigned by text length or modulo counter, producing duplicate questions with conflicting difficulty ratings.
6. **Real Questions Quarantined:** Legitimate technical questions from GitHub sources remain unparsed.
7. **Unusable Embeddings:** All populated embeddings represent full document pollution rather than question semantics.

### CODE PROBLEMS (Must be fixed in the application):
1. **RAG Role Filter Bug:** Filtering on `{'role': 'backend_developer'}` against Title Case `role` metadata.
2. **Query Over-specification:** Ingestion query previously packed category and strategy into vector search queries.
3. **Candidate Validation Gap:** Lack of validation to reject multi-paragraph articles from becoming `QuestionCandidate` objects.
4. **Prompt Leakage in Fallback:** Generator prompt string leaked into live questions.
5. **Disconnected Taxonomies:** Application code maintains a 10-category taxonomy while the vector store only supports `'Coding'` and `'Theory'`.

---

## Part 16 — Final Recommendation & Strategic Decision
### A. Current Database Architecture Summary
The database consists of a functional relational core (`interviews`, `interview_messages`, `code_submissions`) tracked by Alembic (`004_assessment_extensions`), and an unmanaged pgvector table (`document_embeddings`) containing 9,394 rows.

### B. Current document_embeddings Dataset Summary
The question bank is predominantly an uncurated markdown dump from CodeAlpaca, GitHub READMEs, and synthetically generated templates. Only ~686 clean standalone questions exist in the entire table.

### C. Top 10 Dataset Problems
1. 92.5% non-question content.
2. 689 normalized rows are 100% identical synthetic boilerplate.
3. Corrupted string splits (`List (ArrayList`, `LinkedList)`).
4. No `skill` or `technology` taxonomy.
5. Arbitrary difficulty labeling.
6. Round-robin duplicate triads (Easy/Medium/Hard).
7. Corrupted `subtopic` metadata (`## Answer: 1`).
8. Binary category breakdown ('Coding'/'Theory').
9. 4,630 existing embeddings represent polluted text.
10. Legitimate real-world interview questions were bypassed during extraction.

### D. Top 10 Code/RAG Problems
1. `filters['role']` casing mismatch causes zero RAG matches.
2. Vector search query includes non-semantic tokens.
3. No schema validation on RAG candidate length/structure.
4. Leakage of fallback generation prompt instructions into questions.
5. Disconnect between application categories and database categories.
6. `document_embeddings` is not tracked in Alembic migrations.
7. RAG service lacks resilience against malformed metadata payloads.
8. Historical turns stored prompt templates in `interview_messages`.
9. No active verification of embedding vector freshness against text.
10. Lack of canonical skill normalization in the intake layer.

### E. Recommended Canonical Question Schema
Adopt the formal JSON contract outlined in Part 14, separating required pedagogical keys from derived embeddings.

### F. Recommended Skill Taxonomy Approach
Map questions to ESCO canonical skills and role requirements rather than compound strings.

### G. Recommended Difficulty Taxonomy
Difficulty must be assigned based on technical scope (conceptual baseline vs deep trade-offs), not character count.

### H. Recommended Role Taxonomy
Standardize on the 10 canonical snake_case `role_id` keys (`python_developer`, `backend_developer`, etc.).

### I. Recommended Category / Intent / Strategy Taxonomy
Align the database `category` and `intent` fields directly with `QuestionQualityEvaluator`'s 10 categories.

### J. Recommended Ingestion Pipeline
Build a clean ETL pipeline that parses authentic question-and-answer pairs, normalizes skills, validates question syntax, and embeds question-only text.

### K. Recommended Cleanup / Migration Order
1. Fix the RAG role filter code bug in `interview_service.py`.
2. Extract authentic interview questions from the GitHub datasets (JavaScript, React, System Design, DevOps).
3. Discard or repair the 689 synthetic boilerplate records.
4. Restructure `document_embeddings` metadata according to the canonical schema.
5. Generate fresh embeddings for genuine, verified questions.

### L. What Should NOT Be Changed Yet
- Do NOT modify Supabase records.
- Do NOT delete the 6,565 inactive records.
- Do NOT alter RAG similarity thresholds (0.30) or top-k (8).
- Do NOT alter semantic duplicate threshold (0.85).

### M. Are the 689 Normalized Questions Suitable for Embedding?
> **VERDICT: NO.**  
> The 689 questions are 100% synthetic variations of a single sentence template (*'Explain how X operates in the context of Y...'*), frequently with broken formatting like unmatched parentheses. They do not represent authentic interview questions.

### N. Should We Continue with Phase 4.4 or Stop and Redesign?
> **FINAL DECISION: STOP AND REDESIGN.**  
> Do NOT proceed to Phase 4.4 embedding regeneration for the 689 records. Consuming Gemini API embedding quota on synthetic boilerplate would provide zero quality value to InterviewMind AI. We must pause, fix the RAG role filtering bug, and extract authentic interview questions before generating any embeddings.