# Phase 2: Recommended Dataset Architecture

## 1. Multi-Bank Logical Architecture

We should NOT force everything into one table.

### A. Conversational Technical Bank
- Purpose: Standard Q&A, deep dives, scenarios.
- Structure: Questions mapped to Role -> Skill -> Topic -> Intent -> Difficulty.

### B. Coding Tasks Bank
- Purpose: Hands-on code generation or modification (CodeAlpaca-style).
- Structure: Instruction -> Input Spec -> Reference Output -> Language.

### C. System Design Bank
- Purpose: Large, open-ended architecture scenarios.
- Structure: Prompt -> Constraints -> Expected Components -> Scaling requirements.

## 2. Supabase Target Structure

Instead of overloading `document_embeddings`, use:

- `question_sources`: Raw ingestion material (HTML, Markdown, links).
- `question_bank`: The canonical, clean dataset (one row = one question with metadata).
- `question_embeddings`: A 1:1 or 1:N mapping from `question_bank` storing the vector.

## 3. Quality Gates
1. Standalone / Technically meaningful.
2. Authentic or high-quality generation.
3. No markdown pollution or prompt leakage.
4. Valid Intent, Topic, Skill, Role.
