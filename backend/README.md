# InterviewMind AI Backend

Backend web service for the **InterviewMind AI** platform — an AI-powered mock interview system built with FastAPI, LangGraph, SQLAlchemy, and Supabase PostgreSQL.

---

## Unified Architecture

```text
React Frontend (Vite)
     │
     ▼ (REST / CORS)
FastAPI Backend (port 8000)
     │
     ├──────────────────────────┐
     ▼                          ▼
LangGraph AI Engine      Supabase PostgreSQL
(backend/ai_engine)      ├── interviews (Relational)
                         └── interview_messages (Relational)
```

---

## Tech Stack

- **Python 3.12** — Async runtime environment
- **FastAPI** — Web framework with automatic OpenAPI docs
- **SQLAlchemy 2.0 + asyncpg** — Async ORM with PostgreSQL
- **Alembic** — Schema database migrations
- **LangGraph & LangChain** — AI state machine and chain execution
- **Google Gemini API** — LLM response generation
- **Supabase PostgreSQL** — Database storage

---

## Directory Structure

```text
backend/
├── ai_engine/                         # Integrated AI Engine Package
│   ├── chains/                        # Output parsers & evaluation chains
│   ├── graphs/                        # LangGraph state machine & nodes
│   ├── models/                        # Gemini Chat LLM initialization
│   ├── prompts/                       # System prompt templates
│   ├── services/                      # AI Interview & Evaluation services
│   └── vectorstores/                  # Supabase pgvector retriever
├── alembic/                           # Alembic migrations & configuration
│   └── versions/                      # Migration scripts
├── app/                               # FastAPI Application Core
│   ├── api/routes/                    # Health & Interview API routers
│   ├── core/                          # Config, Database, Logging, Middleware
│   ├── models/                        # SQLAlchemy ORM Models
│   ├── providers/ai_provider.py       # AI Provider Facade
│   ├── repositories/                  # Database CRUD layer
│   ├── schemas/                       # Pydantic validation schemas
│   ├── services/                      # Interview Business Logic Service
│   └── utils/                         # Response formatters & helpers
├── tests/                             # Pytest test suite
├── main.py                            # FastAPI Application Entry Point
├── requirements.txt                   # Backend Python Dependencies
├── .env.example                       # Environment Template File
└── README.md                          # Backend Documentation
```

---

## Quick Start

### 1. Set Up Environment Variables

Create `backend/.env` (or copy `.env.example`):
```ini
DATABASE_URL=postgresql://postgres.[REF]:[ENCODED_PASS]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres
DIRECT_URL=postgresql://postgres.[REF]:[ENCODED_PASS]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://[YOUR-PROJECT].supabase.co
SUPABASE_PUBLISHABLE_KEY=your-supabase-publishable-key
SUPABASE_SECRET_KEY=your-supabase-secret-key
GEMINI_API_KEY=your-gemini-api-key
HOST=0.0.0.0
PORT=8000
DEBUG=true
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### 2. Run Database Schema Migrations

Run Alembic schema migrations:
```bash
alembic upgrade head
```

### 3. Start FastAPI Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive API Docs (Swagger)**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Health Check Endpoint**: `http://localhost:8000/api/health`

### 4. Run Pytest Test Suite

```bash
pytest
```
