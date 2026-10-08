# Live Interview Validation Report

**Date:** 2026-10-05 &nbsp;|&nbsp; **Scope:** Validation only. No architecture, ESCO, Question Bank, RAG, or scoring changes. No embedding backfill.
**Environment:** I started a fresh backend from the current code on `127.0.0.1:8010`. The existing server on port 8000 (PID 11964) was left alone because it may be running older code.
**Resume:** `Dinesh_Resume.pdf`, sent through the real `POST /api/interview/resume/upload` endpoint.
**Role:** Backend Developer &nbsp;|&nbsp; **Difficulty:** Medium
**Privacy:** No API keys were printed. Emails, phone numbers, and handles are masked.

---

## Summary

| # | Check | Result |
|---|---|---|
| A | Gemini configuration (keys found, FallbackLLM not used) | **PASS** |
| A2 | Safe diagnostic printed at startup | **PARTIAL** (not printed at startup; checked with a separate probe) |
| B | Resume extraction: the listed artifacts are gone | **PASS** |
| B2 | Resume extraction: other content kept intact | **FAIL** (`Music` becomes `M`, letters split apart, `/heartbeat` artifact) |
| C–E | Three new interviews produced a first question | **PASS** |
| F | First questions vary in a meaningful way | **PARTIAL** |
| G | Source attribution | **PASS** |
| H | Fallback path | **PASS** (one repeated question out of 8 runs) |
| I | No PDF artifacts in the generated questions | **PASS** |
| J | Candidate validation (rejections) | **PASS** (the behaviour changed; explained below) |
| 10 | Final-question cleaning is safe | **FAIL**: real risk shown |
| 11 | Resume analysis gives the same facts each time | **PASS** |
| K | Regression tests | **PASS** (59/59) |

---

## A. Gemini configuration: **PASS** (diagnostic: PARTIAL)

Safe probe run from `backend/` (key values are never read out or printed):

```
GEMINI_API_KEYS env present: False
GEMINI_API_KEY env present: True      <- holds 2 comma-separated keys
Gemini key pool configured: True
Configured key count: 2
LLM class: PoolableLLM
Fallback mode: False
Model: gemini-3.8-flash (default; GEMINI_MODEL is not set)
```

- **Live server log:** the line `"No Gemini API keys found. Using FallbackLLM."` appeared **0** times.
- **Real Gemini calls happened:** `google_genai` logged 3 automatic retries on `503 UNAVAILABLE` ("high demand"), and every call then succeeded. All 3 questions came from Gemini.
- **Working directory:** a script started from `E:\` or the repo root still finds `backend/.env` and gets 2 keys. Only interactive `python -c` or a REPL depends on the current directory: from the repo root it got 0 keys. This is how `python-dotenv` searches for the file, and it does not affect uvicorn.
- **Notes:**
  - `.env` uses the singular `GEMINI_API_KEY` (comma-separated), not `GEMINI_API_KEYS`. The key pool's fallback branch handles this.
  - No startup diagnostic is printed. The LLM module loads lazily on the first question. The `PoolableLLM initialized` INFO line never appears in the server log (0 lines), probably because that logger is not set to INFO.

## B. Resume extraction: removing the listed artifacts **PASS**; keeping content intact **FAIL**

Upload result: 2,315 characters. None of the forbidden markers were found (`laptop-code`, `♂`, `¶usic`, `/envel`, `⌢`).

| Expected to be kept | Seen in the uploaded text |
|---|---|
| Personal Portfolio + AI Assistant | ✅ `Personal Portfolio + AI Assistant (Nuxt + RAG) — Ongoing Major Project` |
| Nuxt, RAG, OpenAI API, Supabase | ✅ `Nuxt 3, Vue, Tailwind, Node API, Supabase (planned), OpenAI API` |
| VibeSync, Flask, MongoDB, Python | ✅ `Flask microservice…`, `MongoDB database`, `Flask (Python ML)` |
| Spacing after `(Nuxt + RAG)` | ✅ `(Nuxt + RAG) — Ongoing` |

**Problems found in the live upload:**

1. **The new cleaner damages real words.** `VibeSync — F ull-Stack M Player with AI Recommendations` and `HEAR T BEA T — Responsive M Player`. The word "**Music**" is cut down to "**M**". The cause is the rule `[\u2640-\u2642\u00b6\u2322/]*usic` in [resume.py:69](file:///e:/interview/backend/app/utils/resume.py#L69). The `*` means the icon prefix is optional, so any occurrence of `usic` gets removed. The `envel[⌢o]pe` rule (line 70) has the same flaw and deletes the word "envelope".
2. **Letters split apart (not fixed):** `F ull-Stack`, `T ech Stack`, `F rontend`, `HEAR T BEA T`.
3. **Another icon artifact (not covered):** `/heartbeatHEAR T BEA T`.
4. **Project inventory is polluted:** the project list holds `"T ech Stack"` and `"Dynamic pages"`. These are a section label and a portfolio feature, not projects. Both were chosen as the **project** for live first questions (see C–E).

## C. Interview 1, Question 1

- **interview_id:** `adc29b24-3054-442c-9218-55e5f5e7c215`
- **source:** `gemini_resume` &nbsp;|&nbsp; **project:** `Dynamic pages` &nbsp;|&nbsp; **technology:** `Node.js`
- **category:** `architecture` &nbsp;|&nbsp; **intent:** `fundamentals` &nbsp;|&nbsp; **difficulty:** Medium &nbsp;|&nbsp; **score:** 51.50
- **reason:** "Probing architecture grounded in verified resume experience for Node.js."
- **Question:**
  > For the dynamic pages in your portfolio—such as Timeline, Achievements, and Gallery—you utilized Node.js on the backend. Could you walk me through the architectural structure of this service? Specifically, how did you define the boundaries between your routing, business logic, and data access layers to keep these content-driven endpoints modular and maintainable?

## D. Interview 2, Question 1

- **interview_id:** `04e3a338-f532-4d00-b892-af823963ea10`
- **source:** `gemini_resume` &nbsp;|&nbsp; **project:** `T ech Stack` ⚠️ &nbsp;|&nbsp; **technology:** `Spring`
- **category:** `role_competency` &nbsp;|&nbsp; **intent:** `debug` &nbsp;|&nbsp; **difficulty:** Medium &nbsp;|&nbsp; **score:** 49.40
- **reason:** "Probing role_competency grounded in verified resume experience for Spring."
- **Rejected candidate:** `[supabase_bank] Question text too short or not a valid question / prompt` (explained in J)
- **Question:**
  > You have Spring listed in your tech stack for backend development alongside REST APIs and SQL databases. When designing backend services in Spring, how do you typically manage transaction boundaries across your service and repository layers? Specifically, walk me through how Spring's proxy-based AOP handles a `@Transactional` method when called internally from another method in the same bean, and how you configure transaction rollback behavior for checked versus unchecked exceptions.

## E. Interview 3, Question 1

- **interview_id:** `0e97c14e-6b30-4f18-b799-0f185aa5c376`
- **source:** `gemini_resume` &nbsp;|&nbsp; **project:** `Dynamic pages` &nbsp;|&nbsp; **technology:** `JavaScript`
- **category:** `trade_offs` &nbsp;|&nbsp; **intent:** `tradeoff` &nbsp;|&nbsp; **difficulty:** Medium &nbsp;|&nbsp; **score:** 48.30
- **reason:** "Probing trade_offs grounded in verified resume experience for JavaScript."
- **Question:**
  > In your portfolio project, you built dynamic pages such as the Timeline, Achievements, and Gallery using JavaScript and Nuxt. What architectural trade-offs did you make when deciding how to fetch and render data for these sections—particularly between Server-Side Rendering (SSR), Static Site Generation (SSG), or client-side fetching—and what compromises did that introduce regarding performance versus content freshness?

## F. Comparison of the three first questions: **PARTIAL**

All values below come from the live `assessment_state.question_history` and the server's `[QUESTION SELECTION]` log.

| Attempt | Project | Technology | Category | Intent (app label) | Exact duplicate |
|---|---|---|---|---|---|
| 1 | Dynamic pages | Node.js | architecture | fundamentals | No |
| 2 | T ech Stack | Spring | role_competency | debug | No |
| 3 | Dynamic pages | JavaScript | trade_offs | tradeoff | No |

| Criterion | Q1 | Q2 | Q3 |
|---|---|---|---|
| Exact text duplicate | No | No | No |
| Same project as another attempt | Yes (Q3) | No | Yes (Q1) |
| Same technology as another attempt | No | No | No |
| Same category as another attempt | No | No | No |
| Intent really different from the others | Yes (architecture/layering) | Yes (transactions/AOP) | Yes (rendering trade-off) |
| Intent label accurate | ⚠️ "fundamentals" for an architecture question | ⚠️ "debug" for a conceptual transactions question | ✅ |
| Grounded in the resume | ✅ Portfolio + Node API | ⚠️ Resume says "Spring Boot (basic)"; the question asks about advanced AOP self-invocation | ✅ Portfolio + Nuxt |
| Relevant to Backend Developer | ✅ | ✅ | ⚠️ Mostly a frontend question (SSR/SSG) |
| Technically sound | ✅ | ✅ | ✅ |
| Clean text | ✅ | ✅ | ✅ |

**Verdict:** The deterministic repetition is fixed. The three questions differ in technology, category, and intent, not just wording. It is only PARTIAL because:

- the "project" chosen was a non-project twice (`Dynamic pages`) and once a section label (`T ech Stack`);
- none of the three questions targeted the main projects (the RAG assistant pipeline or VibeSync's Flask/MongoDB backend), which are the strongest backend evidence on the resume;
- the intent labels are unreliable for 2 of the 3 questions.

## G. Source attribution: **PASS**

- All 3 live winners are labelled `gemini_resume`, and Gemini really produced them (real API calls with 503 retries).
- The rejected candidate kept its label `supabase_bank` and was **not** chosen.
- In the fallback test, all 8 results were labelled `fallback` (see H).

## H. Fallback validation: **PASS** (with one note)

**Setup:** in-process only. I patched `ai_engine.models.llm.llm` to `FallbackLLM()` and made `rag.ask` return `None`. `.env` and the production configuration were not touched. 8 runs with random `interview_id`s, a 3-project inventory, and 8 technologies ([fallback_validate.py](file:///C:/Users/bobby/.gemini/antigravity-ide/brain/8c9d0455-946f-420f-b7e5-064b4f05692a/scratch/fallback_validate.py)).

| Check | Result |
|---|---|
| `source == "fallback"` | ✅ 8/8 |
| Does not claim to be Gemini (text and why_selected) | ✅ `"Deterministic fallback for category …"`, no mention of Gemini |
| Valid question (ends with `?`, on a resume project) | ✅ 8/8 |
| Not always index 0 | ✅ 3/3 projects, 4 technologies, 6 categories used |
| No resume artifacts | ✅ 0 hits |
| Distinct texts | 7/8. Runs #5 and #8 gave the same `api_design` question about Portfolio, because the fallback template ignores the technology |

## I. PDF artifacts in the generated questions: **PASS**

None of the 3 live questions contain `laptop-code`, `♂`, `¶usic`, `/envel`, `⌢`, HTML/markup, `TEXT:`/`SOURCE:` metadata, or `)Letter` spacing errors. The fallback questions are also clean (8/8).

## J. Candidate validation: **PASS** (behaviour changed)

- **Earlier behaviour** (`[gemini_resume] Rejected: Question text too short…`): **not seen** in any of the 3 live interviews. No Gemini candidate was rejected.
- **New behaviour seen once**, in interview 2: `[supabase_bank] Rejected: Question text too short or not a valid question / prompt`.
- **Why it was rejected:** I re-ran the same retrieval read-only (`"Spring role_competency"`, difficulty Medium). It returns a **1,180-character markdown knowledge document**, not a question:
  ```
  ### Concurrency & Async Processing: Deep Dive into Locks
  **Role Focus**: Backend Developer | **Difficulty**: Medium | ...
  ```
  - It has no `?` and does not start with an instruction verb.
  - The `len < 15 or no '?'` rule ([interview_service.py:237](file:///e:/interview/backend/ai_engine/services/interview_service.py#L237)) rejected it correctly. The reason text "too short" is misleading, because the text is long.
- The rejected candidate was **not** selected later; the winner was `gemini_resume`. Attribution stayed correct.
- **Two related findings:**
  - `role_mapping` ([interview_service.py:752-756](file:///e:/interview/backend/ai_engine/services/interview_service.py#L752-L756)) uses snake_case keys (`backend_developer`), but `role_name` is `"Backend Developer"`. As a result, **the Supabase role filter is never applied**.
  - `RAGService.ask` returns `docs[0]` without checking that the document is a question.

## 10. Final-question cleaning design: **FAIL**, real risk shown

[`clean_resume_text`](file:///e:/interview/backend/app/utils/resume.py#L61-L86) runs on every final winning question ([interview_service.py:949](file:///e:/interview/backend/ai_engine/services/interview_service.py#L949)). I ran it on legitimate technical questions ([cleaning_risk_probe.py](file:///C:/Users/bobby/.gemini/antigravity-ide/brain/8c9d0455-946f-420f-b7e5-064b4f05692a/scratch/cleaning_risk_probe.py)): **10 of 11 were changed.**

| Input | Output |
|---|---|
| `design the music recommendation engine` | `design the m recommendation engine` |
| `In your Music Player project…` | `In your M Player project…` |
| `implement a message envelope pattern` | `implement a message pattern` |
| `uploads a file to /envelope/upload` | `uploads a file to /upload` |
| `function f(x)Where x is a list` | `f(x) — Where x is a list` |
| `Promise.all()And Promise.allSettled()` | `Promise.all() — And …` |
| Indented code snippet | indentation and blank lines collapsed |

The risk also reaches the **resume itself**. VibeSync is a music app, so the live upload already reads "M Player". That text then feeds Gemini prompts.

**Recommendation (not implemented; this phase is validation only):**

1. Make the icon rules require an icon prefix instead of making it optional, for example `[\u2640-\u2642\u00b6\u2322/]+(?:laptop-code|usic|envel[\u2322o]pe|heartbeat)`. Or match the known ligature names only when they are stuck directly to a capitalised word.
2. Split the cleaner in two:
   - `normalize_pdf_artifacts(text)`: shared and conservative. It removes only icon code points and prefixed ligature names, and does not touch whitespace inside code.
   - `clean_resume_text`: resume-only. It calls the shared function and also handles social-link dedup, `)Word` → `) — Word` spacing, and whitespace collapse.
3. Apply only `normalize_pdf_artifacts` to generated questions, never the resume-specific rules.
4. Add regression cases for "music", "envelope", `f(x)Where`, and code blocks.

## 11. Resume analysis stability: **PASS**

- `POST /resume/analyze` was called twice with the same resume text and role. The two `data` payloads were **byte-identical** after sorted JSON serialisation (`analysis_stable: true`): same score (63.3), matched areas, missing areas, interview_context (15 items), and feedback.
- Upload/extraction is deterministic (pypdf).
- The variation between the 3 questions therefore comes from the `interview_id` rotation and Gemini, not from the resume being parsed differently.

## K. Tests passed

```
pytest tests/test_pdf_normalization.py tests/test_pdf_artifacts_and_fallback.py \
       tests/test_resume_integration.py tests/test_resume_and_unlimited.py
59 passed in 1.01s
```

The current tests miss the problems above: none check that "music" or "envelope" survive cleaning. Also, `test_pdf_artifacts_and_fallback.py` permanently appends `"mock_key"` to the global `gemini_key_pool.keys`, which leaks into any tests that run after it.

## L. Remaining issues (by priority)

1. **High:** the `usic` / `envel…pe` rules use an optional prefix and corrupt real words ("Music" → "M", "envelope" removed) in both resumes and final questions.
2. **High:** the resume-specific cleaner runs on generated questions and changes valid technical text (`f(x)Where`, code indentation).
3. **Medium:** the project inventory includes non-projects (`T ech Stack`, `Dynamic pages`), which get chosen as the question's "project".
4. **Medium:** the Supabase `role_mapping` key mismatch means the role filter is never applied.
5. **Medium:** RAG can return knowledge documents as "questions". They are rejected correctly, but the bank candidate is wasted. The rejection message "too short" is misleading.
6. **Low:** letter-splitting artifacts (`F ull`, `T ech`, `HEAR T BEA T`) and the `/heartbeat` icon artifact are not handled.
7. **Low:** intent labels are inaccurate for 2 of the 3 live questions (`debug`, `fundamentals`).
8. **Low:** no safe Gemini diagnostic at startup; the `PoolableLLM` INFO log is not visible.
9. **Low:** the fallback template for `api_design` ignores the technology, so the same text repeats for the same project.
10. **Info:** Gemini returned `503 UNAVAILABLE` (model overloaded) three times; the SDK retries recovered each time. Supabase REST RPC dropped once and the direct-DB fallback worked.
11. **Info:** `test_pdf_artifacts_and_fallback.py` changes the global key pool, which can affect other tests.

---

**Artifacts:** [live_results.json](file:///C:/Users/bobby/.gemini/antigravity-ide/brain/8c9d0455-946f-420f-b7e5-064b4f05692a/scratch/live_results.json) · [live_backend.log](file:///C:/Users/bobby/.gemini/antigravity-ide/brain/8c9d0455-946f-420f-b7e5-064b4f05692a/scratch/live_backend.log) · [live_validate.py](file:///C:/Users/bobby/.gemini/antigravity-ide/brain/8c9d0455-946f-420f-b7e5-064b4f05692a/scratch/live_validate.py) · [repro_rejected_bank.py](file:///C:/Users/bobby/.gemini/antigravity-ide/brain/8c9d0455-946f-420f-b7e5-064b4f05692a/scratch/repro_rejected_bank.py)

**No code was changed in this phase.** The temporary server on port 8010 has been stopped.
