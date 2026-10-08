import json
import os

def generate_markdown_report():
    with open("reports/database_dataset_forensic_audit.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    md = []
    
    md.append("# Phase 0: Complete Database & Dataset Forensic Audit Report")
    md.append("**InterviewMind AI — Backend & Vector Database Audit**\n")
    md.append("> **CRITICAL SAFETY DIRECTIVE COMPLIANCE:** This audit was conducted entirely in **READ-ONLY** mode. Zero database mutations (INSERT/UPDATE/DELETE/ALTER), zero embedding regenerations, and **0 Gemini API calls** were made.\n")
    
    # Executive Summary
    md.append("## Executive Summary")
    md.append("This forensic audit investigated the real Supabase PostgreSQL database, its underlying dataset (`document_embeddings`), relational tables (`interviews`, `interview_messages`, `code_submissions`, `alembic_version`), and application integration layers.")
    md.append("\n### High-Impact Forensic Findings:")
    md.append("1. **The 689 'Normalized Questions' are 100% Synthetic Boilerplate:** All 689 questions extracted during Phase 4.1/4.2 originate from a single synthetic generator script (`dataset_generator.py`) and share an identical sentence template: *'Explain how {subtopic} operates in the context of {topic}... What are the primary trade-offs...'* Many suffer from string-splitting defects resulting in corrupted syntax (e.g., `List (ArrayList`, `LinkedList)`). **Embedding these 689 rows would waste API quota on synthetic artifacts rather than real interview questions.**")
    md.append("2. **Real Interview Questions Were Excluded:** Authentic interview questions from GitHub repositories (e.g., `javascript-interview-questions`, `reactjs-interview-questions`, `system-design-primer`, `devops-exercises`) were either quarantined as tutorials or left unextracted because extraction heuristics strictly looked for `**Question**:` markers that only existed in synthetic templates.")
    md.append("3. **Critical RAG Role Filter Bug in Code:** In `document_embeddings`, the role metadata stores Title Case values (e.g. `'Backend Developer'`) in the `role` field, while snake_case (e.g. `'backend_developer'`) is stored in `role_id`. However, `InterviewService` creates filters as `{'role': 'backend_developer'}`. Because PostgreSQL JSONB containment `@>` requires exact string matching, **RAG role-filtered queries return 0 results**.")
    md.append("4. **Unscientific Difficulty Assignment:** Difficulty labels in the dataset are not human-calibrated. In scraped data, difficulty was assigned purely on character length (>800 chars = 'Hard'). In synthetic data, difficulty was cycled round-robin (`i % 3`), creating 129 identical duplicate question groups labeled simultaneously as Easy, Medium, and Hard.")
    md.append("5. **Missing Taxonomy Fields:** There are **zero** `skill`, `technology`, `intent`, or `strategy` fields in `document_embeddings.metadata`. The `subtopic` field is severely corrupted (containing 6,571 distinct values, mostly raw markdown headers like `## Answer: 1`).")
    md.append("\n---\n")

    # Part 1
    md.append("## Part 1 — Database Schema Inventory")
    md.append("The database currently contains 5 public tables and 3 vector search RPC functions.\n")
    
    inventory = data["part_1_schema_inventory"]
    for tbl_name, tbl in inventory.items():
        md.append(f"### Table: `public.{tbl_name}`")
        md.append(f"- **Row Count:** {tbl['row_count']}")
        md.append(f"- **Primary Key:** `{', '.join(tbl['primary_key']) if tbl['primary_key'] else 'None'}`")
        md.append(f"- **RLS Enabled:** `{tbl['rls_enabled']}` | **RLS Forced:** `{tbl['rls_forced']}`")
        md.append(f"- **RLS Policies:** {len(tbl['rls_policies'])} defined (No policies exist; table relies on database superuser / service_role bypass)")
        
        md.append("\n**Columns:**")
        md.append("| Column | Data Type (UDT) | Nullable | Default |")
        md.append("|---|---|---|---|")
        for c in tbl["columns"]:
            md.append(f"| `{c['column_name']}` | `{c['data_type']}` (`{c['udt_name']}`) | `{c['is_nullable']}` | `{c['column_default'] or 'None'}` |")
            
        if tbl["foreign_keys"]:
            md.append("\n**Foreign Keys:**")
            for fk in tbl["foreign_keys"]:
                md.append(f"- `{fk['column_name']}` &rarr; `public.{fk['foreign_table_name']}({fk['foreign_column_name']})` (ON DELETE: `{fk['delete_rule']}`, ON UPDATE: `{fk['update_rule']}`)")
                
        if tbl["indexes"]:
            md.append("\n**Indexes:**")
            for idx in tbl["indexes"]:
                md.append(f"- `{idx['indexname']}`: `{idx['indexdef']}`")
                
        md.append("\n")

    md.append("### Database RPC Functions (Vector Search)")
    for rpc in data["part_1_rpcs"]:
        md.append(f"#### Function: `{rpc['proname']}`")
        md.append("```sql")
        md.append(rpc["def"])
        md.append("```\n")

    # Part 2
    md.append("## Part 2 — Relationship Map")
    md.append("### Formal Relational Constraints (PostgreSQL FKs)")
    md.append("```mermaid")
    md.append("graph TD")
    md.append("    interviews -->|1:N (CASCADE)| interview_messages")
    md.append("    interviews -->|1:N (CASCADE)| code_submissions")
    md.append("    alembic_version[alembic_version (Isolated)]")
    md.append("    document_embeddings[document_embeddings (Isolated Vector Store)]")
    md.append("```")
    md.append("\n### Architectural Connection Analysis")
    md.append("1. **Core Relational Core:** `interviews` acts as the root entity. Both `interview_messages` and `code_submissions` have explicit foreign keys to `interviews.id` with `ON DELETE CASCADE`.")
    md.append("2. **`alembic_version`:** Independent migration tracking table managed by SQLAlchemy/Alembic. Currently recorded at migration `004_assessment_extensions`.")
    md.append("3. **`document_embeddings` is NOT formally related:** `document_embeddings` has **ZERO** foreign key constraints linking to `interviews` or any other table. It is NOT managed by Alembic migrations (it was initialized via standalone SQL script `alembic/pgvector_setup.sql`).")
    md.append("4. **Application-Level Coupling:** The connection between `document_embeddings` and `interview_messages` exists exclusively in application memory:")
    md.append("   - At runtime, `InterviewService.generate_question()` calls `RAGService.ask()`.")
    md.append("   - `RAGService` retrieves rows from `document_embeddings` via `SupabaseVectorRetriever`.")
    md.append("   - If selected by `QuestionQualityEvaluator`, the question string is populated in a `QuestionCandidate` and subsequently written into `interview_messages.question` upon saving the turn.")
    md.append("\n---\n")

    # Part 3
    md.append("## Part 3 — document_embeddings Forensic Audit")
    doc_audit = data["part_3_document_embeddings_audit"]
    md.append(f"- **Total Rows in Dataset:** {doc_audit['total_rows']:,}")
    md.append(f"- **Populated Embeddings:** {doc_audit['populated_embeddings']:,} (49.3%)")
    md.append(f"- **NULL Embeddings:** {doc_audit['null_embeddings']:,} (50.7%)")
    md.append(f"- **Active Records:** {doc_audit['status_breakdown']['active']} (0%)")
    md.append(f"- **Inactive / Quarantined Records:** {doc_audit['status_breakdown']['inactive']:,} (81.6%)")
    md.append(f"- **Unspecified Status Records:** {doc_audit['status_breakdown']['null_or_unspecified']:,} (18.4%)")
    
    md.append("\n### Question Data Quality Classification (Heuristic Audit)")
    md.append("| Classification Category | Row Count | Percentage | Description |")
    md.append("|---|---|---|---|")
    class_bd = doc_audit["quality_classifications"]
    descriptions = {
        "CLEAN QUESTION": "Short, standalone questions ending with '?' without markdown fences or answers.",
        "QUESTION WITH METADATA": "Questions that include contextual headings or brief intro notes.",
        "QUESTION + ANSWER": "Records that explicitly bundle the question and the model answer/solution.",
        "QUESTION + RUBRIC": "Records containing explicit evaluation criteria, scoring, or candidate rubrics.",
        "FULL TUTORIAL/ARTICLE": "Comprehensive articles or documentation chapters exceeding 250 words.",
        "EXPLANATION WITHOUT QUESTION": "Theoretical explanations, notes, or concept deep-dives without an actual question.",
        "CODE EXAMPLE WITHOUT QUESTION": "Stand-alone code snippets or syntax demonstrations lacking an interview prompt.",
        "UNKNOWN": "Records with unstructured or mixed syntax patterns."
    }
    for cat, cnt in sorted(class_bd.items(), key=lambda x: x[1], reverse=True):
        desc = descriptions.get(cat, "Audit category")
        pct = (cnt / doc_audit['total_rows']) * 100
        md.append(f"| **{cat}** | {cnt:,} | {pct:.1f}% | {desc} |")
        
    md.append("\n> **Forensic Reality:** Less than 7.5% of the database represents clean, standalone interview questions. Over 92% of the dataset consists of model answers, rubrics, full tutorials, and explanatory documentation.")
    md.append("\n---\n")

    # Part 4
    md.append("## Part 4 — Actual Dataset Schema (Metadata Fields)")
    md.append("| Field Name | Present Count | Null Rate | Distinct Values | Sample Values / Description | Quality Problems |")
    md.append("|---|---|---|---|---|---|")
    for fld, info in data["part_4_actual_dataset_schema"].items():
        present = info["present_count"]
        null_rate = (info["null_or_empty_count"] / 9394) * 100
        samples = ", ".join([f"'{s}'" for s in info["sample_values"][:3]]) if info["sample_values"] else "None"
        distinct = info["distinct_values"]
        
        problems = "None"
        if present == 0:
            problems = "Field completely missing from metadata."
        elif fld == "subtopic":
            problems = "Severe markdown pollution (headers like '## Answer: 1')."
        elif fld == "category":
            problems = "Virtually binary ('Coding' vs 'Theory') despite 10 code categories."
        elif fld == "difficulty":
            problems = "Assigned via character length or round-robin loop."
        elif fld == "role":
            problems = "Title Case ('Backend Developer') conflicts with snake_case code filter."
            
        md.append(f"| `{fld}` | {present:,} | {null_rate:.1f}% | {distinct:,} | {samples} | {problems} |")
        
    md.append("\n---\n")

    # Part 5
    md.append("## Part 5 — Skill Analysis")
    skill_info = data["part_5_skill_analysis"]
    md.append("- **Total Distinct Topics:** 137 (100 in primary curated set)")
    md.append("- **Is there a `skill` field?** **NO.** There is no field named `skill` or `technology` in metadata.")
    md.append("\n### Distribution & Concept Analysis:")
    md.append("1. **Compound Multi-Concept Fields:** Instead of atomic skills (e.g. `'Python'`, `'SQL'`, `'React'`), `topic` values combine technology, exercise type, and discipline:")
    md.append("   - `'Python Algorithms & Data Structures'` (2,272 rows)")
    md.append("   - `'JavaScript / DOM / React Tasks'` (754 rows)")
    md.append("   - `'Bash & Automation Scripts'` (86 rows)")
    md.append("   - `'SQL Queries & Schema Design'` (457 rows)")
    md.append("2. **Duplicate & Overlapping Concepts:** Multiple topics refer to the same domain with differing granularity:")
    md.append("   - `'JavaScript / DOM / React Tasks'` (754) vs `'JavaScript Core & DOM'` (716) vs `'JavaScript Core & ES6+'` (44)")
    md.append("   - `'React & Hooks'` (581) vs `'React Component Tasks'` (47)")
    md.append("   - `'SQL Queries & Schema Design'` (457) vs `'SQL Analytical Queries'` (15) vs `'Data Analytics & SQL Queries'` (74)")
    md.append("   - `'Cloud Computing & AWS'` (61) vs `'Cloud Computing Fundamentals (AWS/Azure/GCP)'` (44)")
    md.append("3. **Massive Representation Imbalance:**")
    md.append("   - A single topic (`'Python Algorithms & Data Structures'`) accounts for **24.2%** of the entire database.")
    md.append("   - Meanwhile, 38 specialized topics contain exactly 15 records each, and crucial disciplines like CI/CD contain only 5 records.")
    md.append("\n---\n")

    # Part 6
    md.append("## Part 6 — Question Quality Analysis")
    q_patterns = data["part_6_question_quality_analysis"]["text_patterns"]
    md.append("### Global Text Syntax Metrics:")
    md.append(f"- **Questions ending with '?':** {q_patterns['ends_with_question_mark']:,} (7.3%)")
    md.append(f"- **Records containing '?' elsewhere:** {q_patterns['contains_question_mark_not_at_end']:,} (17.3%)")
    md.append(f"- **Records with NO '?' anywhere:** {q_patterns['no_question_mark_anywhere']:,} (75.4%)")
    md.append(f"- **Records with Markdown Code Fences (` ``` `):** {q_patterns['has_markdown_code']:,} (62.4%)")
    md.append(f"- **Records with Markdown Headings (`#`, `##`, `###`):** {q_patterns['has_markdown_header']:,} (92.6%)")
    md.append(f"- **Records with Model Answer Markers:** {q_patterns['has_answer_marker']:,}")
    md.append(f"- **Records with Rubric Markers:** {q_patterns['has_rubric_marker']:,}")
    md.append(f"- **Records over 1,000 characters:** {q_patterns['very_long_records_gt_1000_chars']:,}")

    md.append("\n### Concrete Examples of Problem Categories in the Database:")
    defects = data["part_6_question_quality_analysis"]["defect_samples"]
    
    if defects.get("no_question_mark"):
        sample_nq = defects["no_question_mark"][0]
        md.append(f"\n#### 1. Non-Question Explanation (Missing '?')\n> **ID:** `{sample_nq['id']}` | **Topic:** `{sample_nq['topic']}`  \n> *\"{sample_nq['content']}\"*")

    if defects.get("explain_template_boilerplate"):
        sample_boil = defects["explain_template_boilerplate"][0]
        md.append(f"\n#### 2. Synthetic Template Boilerplate\n> **ID:** `{sample_boil['id']}` | **Topic:** `{sample_boil['topic']}`  \n> *\"{sample_boil['content_preview']}\"*")

    if defects.get("contains_answer_block"):
        sample_ans = defects["contains_answer_block"][0]
        md.append(f"\n#### 3. Full Document Bundling Question + Answer\n> **ID:** `{sample_ans['id']}` | **Topic:** `{sample_ans['topic']}`  \n> *\"{sample_ans['content_preview']}\"*")

    if defects.get("write_a_program_template"):
        sample_code = defects["write_a_program_template"][0]
        md.append(f"\n#### 4. Code Generation Instruction Prompt (CodeAlpaca style)\n> **ID:** `{sample_code['id']}` | **Topic:** `{sample_code['topic']}`  \n> *\"{sample_code['content_preview']}\"*")

    if defects.get("scenario_template_p99"):
        sample_scen = defects["scenario_template_p99"][0]
        md.append(f"\n#### 5. Fake Production Scenario Template\n> **ID:** `{sample_scen['id']}` | **Topic:** `{sample_scen['topic']}`  \n> *\"{sample_scen['content_preview']}\"*")


    md.append("\n---\n")

    # Part 7
    md.append("## Part 7 — Difficulty Analysis")
    diff_dist = data["part_7_difficulty_analysis"]["distribution"]
    md.append("| Difficulty Level | Record Count | Percentage |")
    md.append("|---|---|---|")
    for d_val, cnt in diff_dist.items():
        pct = (cnt / 9394) * 100
        md.append(f"| **{d_val}** | {cnt:,} | {pct:.1f}% |")
    md.append("| **NULL / Missing** | 6 | 0.1% |")
    
    md.append("\n### Forensic Findings on Difficulty Reliability:")
    md.append("1. **Not Pedagogically Valid:** The difficulty values in the database are completely untrustworthy.")
    md.append("2. **Length-Based Assignment:** In `download_and_clean_real_dataset.py`, difficulty was assigned purely on text length:")
    md.append("   ```python")
    md.append("   if len(body_clean) > 800 or '```' in body_clean: difficulty = 'Hard'")
    md.append("   elif len(body_clean) > 350: difficulty = 'Medium'")
    md.append("   else: difficulty = 'Easy'")
    md.append("   ```")
    md.append("   This means a simple concept with a verbose explanation was labeled 'Hard', while an intrinsically difficult concept explained concisely was labeled 'Easy'.")
    md.append("3. **Round-Robin Modulo Assignment:** In `dataset_generator.py`, synthetic entries cycled `['Easy', 'Medium', 'Hard'][i % 3]`. This produced identical questions labeled as 'Easy', 'Medium', and 'Hard' across different rows.")
    md.append("\n---\n")

    # Part 8
    md.append("## Part 8 — Role Analysis")
    role_dist = data["part_8_role_analysis"]["distribution"]
    md.append("| Role Title | Record Count | `role_id` Equivalent |")
    md.append("|---|---|---|")
    for r_val, cnt in role_dist.items():
        rid = r_val.lower().replace(" ", "_").replace("/", "").replace("  ", " ").strip()
        md.append(f"| **{r_val}** | {cnt:,} | `{rid}` |")
        
    md.append("\n### Critical Bug: Role Metadata Mismatch")
    md.append("- In database metadata, the `role` key stores Title Case strings (e.g. `'Backend Developer'`), and the `role_id` key stores snake_case strings (e.g. `'backend_developer'`).")
    md.append("- In application code (`interview_service.py`), the RAG filter is constructed as:")
    md.append("  ```python")
    md.append("  mapped_role = role_name.strip().lower().replace(' ', '_').replace('-', '_')")
    md.append("  filters['role'] = mapped_role  # e.g. 'backend_developer'")
    md.append("  ```")
    md.append("- This submits `metadata @> '{\"role\": \"backend_developer\"}'` to Supabase PostgreSQL.")
    md.append("- **Result:** ZERO records match. Whenever `filters['role']` was applied, RAG silently returned empty results and fell through to Gemini generation.")
    md.append("\n---\n")

    # Part 9
    md.append("## Part 9 — Category / Intent / Strategy Analysis")
    md.append("### In the Database:")
    md.append("- **Category:** Only two categories dominate: `'Coding'` (5,313 records, 56.6%) and `'Theory'` (4,075 records, 43.4%), with 5 scattered legacy records.")
    md.append("- **Intent:** `0` records possess an `intent` field.")
    md.append("- **Strategy:** `0` records possess a `strategy` field.")
    md.append("\n### In Application Code (`interview_service.py` & `QuestionQualityEvaluator`):")
    md.append("- The application defines a rich 10-category taxonomy: `architecture`, `data_flow`, `implementation`, `technology_choice`, `database_design`, `api_design`, `security`, `debugging_profiling`, `tradeoff_analysis`, `role_competency`.")
    md.append("- The application also models pedagogical intents: `explain`, `tradeoff`, `debug`, `design`, `deepen`, `validate`.")
    md.append("- **Disconnection:** Because none of these exist in `document_embeddings`, the vector database cannot participate in category rotation or intent-driven question selection.")
    md.append("\n---\n")

    # Part 10
    md.append("## Part 10 — Embedding Audit")
    emb_data = data["part_10_embedding_audit"]
    md.append(f"- **Vector Dimensions:** {emb_data['dimensions']}")
    md.append(f"- **Populated Embeddings:** {emb_data['populated_count']:,}")
    md.append(f"- **NULL Embeddings:** {emb_data['null_count']:,}")
    md.append("- **Embedding Model:** `gemini-embedding-2` (not tracked in database metadata)")
    md.append("\n### Key Forensic Finding:")
    md.append("- The 4,630 existing non-null embeddings were computed over the **entire raw document text** (`content`), including markdown headers, model answers, code snippets, and evaluation rubrics.")
    md.append("- They do NOT represent the semantic vector of an interview question.")
    md.append("- When searching for question semantics (e.g. *'How does garbage collection work in Python?'*), the vector compares against the embedding of an entire multi-section document, degrading cosine similarity precision.")
    md.append("- **Existing embeddings cannot be reused** once questions are normalized.")
    md.append("\n---\n")

    # Part 11
    md.append("## Part 11 — Duplicate Analysis")
    dups = data["part_11_duplicate_analysis"]
    md.append(f"- **Exact Duplicate Groups:** {dups['total_duplicate_groups']}")
    md.append(f"- **Affected Records in Duplicate Groups:** {dups['total_affected_records']}")
    md.append(f"- **Groups Differing Only in Difficulty:** {dups['groups_with_diff_difficulty']} (100% of duplicate groups!)")
    md.append(f"- **Groups Differing in Role:** {dups['groups_with_diff_roles']}")
    md.append(f"- **Groups Differing in Topic:** {dups['groups_with_diff_topics']}")
    md.append("\n### Forensic Significance:")
    md.append("Every single duplicate group in the dataset is an artifact of the synthetic generator's round-robin difficulty loop. The exact same question text was generated three times and labeled 'Easy', 'Medium', and 'Hard'.")
    md.append("Example duplicate triad:")
    md.append("```")
    md.append("Question: 'Explain how Linked list cycle detection operates in the context of DSA & Problem Solving. What are the primary trade-offs when choosing this approach...'")
    md.append("  - Row 1 (e2b7dcec): Difficulty = 'Easy'")
    md.append("  - Row 2 (464abf7d): Difficulty = 'Medium'")
    md.append("  - Row 3 (44d76be5): Difficulty = 'Hard'")
    md.append("```\n")

    # Part 12
    md.append("## Part 12 — Other Tables Audit")
    md.append("### 1. `public.interviews` (139 rows)")
    md.append("- Tracks candidate sessions. Active interviews: 95, Completed: 44.")
    md.append("- Roles exhibit case/naming inconsistency: `'Backend Developer'` (23), `'Frontend developer'` (16), `'SOFTWARE ENGINEER'` (15), `'Software Developer'` (13).")
    md.append("- Topic column contains unnormalized strings, including full role descriptions (e.g. `'Frontend Developer: JavaScript, TypeScript, React, HTML, CSS, browser fundamentals, REST APIs...'`).")
    md.append("\n### 2. `public.interview_messages` (278 rows)")
    md.append("- 238 out of 278 rows (85.6%) have NULL `question_type` and NULL `question_difficulty`.")
    md.append("- **Prompt Leakage Artifacts:** Past questions stored in `interview_messages` show severe prompt leakage:")
    md.append("  > *\"Can you explain the core principles of Generate one Easy level interview question on Python. Return only JSON. ?\"*")
    md.append("\n### 3. `public.code_submissions` (0 rows)")
    md.append("- Schema exists (`interview_id`, `problem_id`, `language`, `source_code`, `result`), currently unpopulated.")
    md.append("\n---\n")

    # Part 13
    md.append("## Part 13 — Application &harr; Database Mapping")
    md.append("### Data Flow Analysis:")
    md.append("1. **Write Path:** `document_embeddings` is populated via offline batch scripts (`ingest.py`, `ingest_bulk.py`). It is NOT written during live interview turns.")
    md.append("2. **Read Path:** `interview_service.py` calls `RAGService.ask()` -> `SupabaseVectorRetriever` -> PostgREST RPC `match_document_embeddings_filtered` -> `public.document_embeddings`.")
    md.append("3. **Mismatch Point 1 (Role Filter):** Code passes `filters['role'] = snake_case`, but DB stores Title Case in `role` and snake_case in `role_id`.")
    md.append("4. **Mismatch Point 2 (Content Expectations):** Code expects `doc.page_content` to be a concise question. In reality, it receives multi-paragraph markdown documents.")
    md.append("5. **Mismatch Point 3 (Fallback Dependency):** Because RAG queries often failed due to the role filter bug or returned unparseable multi-paragraph tutorials rejected by `QuestionQualityEvaluator`, the system continually fell through to Gemini generation.")
    md.append("\n---\n")

    # Part 14
    md.append("## Part 14 — Ideal Dataset Contract")
    md.append("To establish a robust question bank for InterviewMind AI, each canonical question record should adhere to the following schema:\n")
    md.append("```json")
    md.append("""{
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
}""")
    md.append("```\n")
    md.append("### Contract Division:")
    md.append("- **REQUIRED:** `id`, `question`, `role_id`, `primary_skill`, `difficulty`, `category`, `intent`, `status`.")
    md.append("- **OPTIONAL:** `secondary_skills`, `expected_answer`, `evaluation_rubric`, `source`.")
    md.append("- **DERIVED:** `embedding` (generated from `question`), `token_count`, timestamps.")
    md.append("- **NOT NEEDED / PROHIBITED:** Multi-paragraph tutorial markdown blocks, synthetic boilerplate templates, pseudo-code demos.")
    md.append("\n---\n")

    # Part 15
    md.append("## Part 15 — Dataset Problems vs. Code Problems")
    md.append("### DATASET PROBLEMS (Must be fixed in the data):")
    md.append("1. **Data Pollution:** 92.5% of `document_embeddings` rows contain tutorials, rubrics, and model answers rather than questions.")
    md.append("2. **Synthetic Template Monotony:** The 689 normalized rows are 100% identical synthetic sentences with broken string splits (e.g. `List (ArrayList`).")
    md.append("3. **Missing Canonical Skills:** Metadata lacks `skill` and `technology` fields entirely.")
    md.append("4. **Corrupted Subtopics:** 6,571 subtopic values contaminated by markdown heading fragments.")
    md.append("5. **Arbitrary Difficulty Labels:** Difficulty assigned by text length or modulo counter, producing duplicate questions with conflicting difficulty ratings.")
    md.append("6. **Real Questions Quarantined:** Legitimate technical questions from GitHub sources remain unparsed.")
    md.append("7. **Unusable Embeddings:** All populated embeddings represent full document pollution rather than question semantics.")

    md.append("\n### CODE PROBLEMS (Must be fixed in the application):")
    md.append("1. **RAG Role Filter Bug:** Filtering on `{'role': 'backend_developer'}` against Title Case `role` metadata.")
    md.append("2. **Query Over-specification:** Ingestion query previously packed category and strategy into vector search queries.")
    md.append("3. **Candidate Validation Gap:** Lack of validation to reject multi-paragraph articles from becoming `QuestionCandidate` objects.")
    md.append("4. **Prompt Leakage in Fallback:** Generator prompt string leaked into live questions.")
    md.append("5. **Disconnected Taxonomies:** Application code maintains a 10-category taxonomy while the vector store only supports `'Coding'` and `'Theory'`.")
    md.append("\n---\n")

    # Part 16
    md.append("## Part 16 — Final Recommendation & Strategic Decision")
    md.append("### A. Current Database Architecture Summary")
    md.append("The database consists of a functional relational core (`interviews`, `interview_messages`, `code_submissions`) tracked by Alembic (`004_assessment_extensions`), and an unmanaged pgvector table (`document_embeddings`) containing 9,394 rows.")
    md.append("\n### B. Current document_embeddings Dataset Summary")
    md.append("The question bank is predominantly an uncurated markdown dump from CodeAlpaca, GitHub READMEs, and synthetically generated templates. Only ~686 clean standalone questions exist in the entire table.")
    md.append("\n### C. Top 10 Dataset Problems")
    md.append("1. 92.5% non-question content.")
    md.append("2. 689 normalized rows are 100% identical synthetic boilerplate.")
    md.append("3. Corrupted string splits (`List (ArrayList`, `LinkedList)`).")
    md.append("4. No `skill` or `technology` taxonomy.")
    md.append("5. Arbitrary difficulty labeling.")
    md.append("6. Round-robin duplicate triads (Easy/Medium/Hard).")
    md.append("7. Corrupted `subtopic` metadata (`## Answer: 1`).")
    md.append("8. Binary category breakdown ('Coding'/'Theory').")
    md.append("9. 4,630 existing embeddings represent polluted text.")
    md.append("10. Legitimate real-world interview questions were bypassed during extraction.")
    md.append("\n### D. Top 10 Code/RAG Problems")
    md.append("1. `filters['role']` casing mismatch causes zero RAG matches.")
    md.append("2. Vector search query includes non-semantic tokens.")
    md.append("3. No schema validation on RAG candidate length/structure.")
    md.append("4. Leakage of fallback generation prompt instructions into questions.")
    md.append("5. Disconnect between application categories and database categories.")
    md.append("6. `document_embeddings` is not tracked in Alembic migrations.")
    md.append("7. RAG service lacks resilience against malformed metadata payloads.")
    md.append("8. Historical turns stored prompt templates in `interview_messages`.")
    md.append("9. No active verification of embedding vector freshness against text.")
    md.append("10. Lack of canonical skill normalization in the intake layer.")
    md.append("\n### E. Recommended Canonical Question Schema")
    md.append("Adopt the formal JSON contract outlined in Part 14, separating required pedagogical keys from derived embeddings.")
    md.append("\n### F. Recommended Skill Taxonomy Approach")
    md.append("Map questions to ESCO canonical skills and role requirements rather than compound strings.")
    md.append("\n### G. Recommended Difficulty Taxonomy")
    md.append("Difficulty must be assigned based on technical scope (conceptual baseline vs deep trade-offs), not character count.")
    md.append("\n### H. Recommended Role Taxonomy")
    md.append("Standardize on the 10 canonical snake_case `role_id` keys (`python_developer`, `backend_developer`, etc.).")
    md.append("\n### I. Recommended Category / Intent / Strategy Taxonomy")
    md.append("Align the database `category` and `intent` fields directly with `QuestionQualityEvaluator`'s 10 categories.")
    md.append("\n### J. Recommended Ingestion Pipeline")
    md.append("Build a clean ETL pipeline that parses authentic question-and-answer pairs, normalizes skills, validates question syntax, and embeds question-only text.")
    md.append("\n### K. Recommended Cleanup / Migration Order")
    md.append("1. Fix the RAG role filter code bug in `interview_service.py`.")
    md.append("2. Extract authentic interview questions from the GitHub datasets (JavaScript, React, System Design, DevOps).")
    md.append("3. Discard or repair the 689 synthetic boilerplate records.")
    md.append("4. Restructure `document_embeddings` metadata according to the canonical schema.")
    md.append("5. Generate fresh embeddings for genuine, verified questions.")
    md.append("\n### L. What Should NOT Be Changed Yet")
    md.append("- Do NOT modify Supabase records.")
    md.append("- Do NOT delete the 6,565 inactive records.")
    md.append("- Do NOT alter RAG similarity thresholds (0.30) or top-k (8).")
    md.append("- Do NOT alter semantic duplicate threshold (0.85).")
    md.append("\n### M. Are the 689 Normalized Questions Suitable for Embedding?")
    md.append("> **VERDICT: NO.**  \n> The 689 questions are 100% synthetic variations of a single sentence template (*'Explain how X operates in the context of Y...'*), frequently with broken formatting like unmatched parentheses. They do not represent authentic interview questions.")
    md.append("\n### N. Should We Continue with Phase 4.4 or Stop and Redesign?")
    md.append("> **FINAL DECISION: STOP AND REDESIGN.**  \n> Do NOT proceed to Phase 4.4 embedding regeneration for the 689 records. Consuming Gemini API embedding quota on synthetic boilerplate would provide zero quality value to InterviewMind AI. We must pause, fix the RAG role filtering bug, and extract authentic interview questions before generating any embeddings.")
    
    report_content = "\n".join(md)
    out_path = "reports/database_dataset_forensic_audit.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Saved human-readable audit report to {out_path}")

if __name__ == "__main__":
    generate_markdown_report()
