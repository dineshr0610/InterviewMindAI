# InterviewMind AI Project Guardrails

## Project architecture

InterviewMind AI uses a React/Vite frontend, FastAPI backend, Supabase PostgreSQL with pgvector, Gemini-based AI services, and LangGraph orchestration. The public interview API is implemented under `backend/app/`; the protected AI engine is under `backend/ai_engine/`.

## Team responsibilities

Work only within the assigned task. Preserve existing worktree changes unless a demonstrated, in-scope bug requires the smallest safe change.

## Week 1 requirements and acceptance criteria

Week 1 covers the technical interview flow: topic-locked adaptive questions, answer evaluation, difficulty adaptation, history, RAG, LangGraph runtime verification, frontend/backend integration, final results, validation, and automated verification. Week 1 must be completed and verified before any Week 2 work begins. Do not claim completion without verification.

## Week 2 and Week 3 boundaries

Do not implement Week 2 or Week 3 features. Their detailed requirements are intentionally not defined in this file.

## Global development rules

- Do not perform unnecessary refactoring.
- Test every change.
- Preserve compatible public API contracts unless an approved requirement requires a change.
- Do not claim completion without verification.

## Protected files and code

Gunal's `backend/ai_engine/` is protected. Do not rewrite, restructure, replace, or remove it. Modify it only for a demonstrated Week 1 acceptance bug, using the smallest safe change.

## Git workflow rules

- Inspect `git status` before changes.
- Preserve unrelated changes.
- Run `git diff --check` before handoff.
- Do not commit unless explicitly asked.

## Security and secrets rules

- Do not commit secrets, `.env` files, API keys, database credentials, generated logs, or temporary files.
- Do not expose credentials in commands, output, or reports.
