# InterviewMind AI — Production-Grade AI Interview Platform

**InterviewMind AI** is an end-to-end, full-stack mock technical interview platform powered by **FastAPI**, **React + Vite**, **LangGraph**, and **Google Gemini AI**, backed by **Supabase PostgreSQL**.

---

## 1. Project Overview

InterviewMind AI automates technical interviewing by generating adaptive, role-specific questions and providing real-time evaluation feedback (scores, strengths, improvements, and follow-up questions). The platform adapts question difficulty based on candidate performance and maintains complete interview history transcripts.

---

## 2. Core Features

- **Adaptive Question Generation**: Dynamically crafts interview questions based on topic, role, and difficulty level (Easy, Medium, Hard).
- **Intelligent Answer Evaluation**: Scores candidate responses on a scale of 1-10 with detailed feedback, strengths, and area-for-improvement recommendations.
- **LangGraph AI Engine Integration**: Modular AI agent workflow built with state graphs and LLM chains.
- **Supabase PostgreSQL & Vector Store**: Fully asynchronous ORM with Alembic schema migration control and pgvector integration.
- **Interactive OpenAPI Documentation**: Built-in Swagger UI and ReDoc interface for all REST endpoints.
- **Production-Ready Architecture**: Decoupled frontend (Vercel) and backend (Render) setup with fallback rule-based evaluation safeguards.

---

## 3. System Architecture Diagram

```mermaid
flowchart TD
    subgraph Client ["Frontend (Vercel)"]
        UI["React + Vite + TypeScript"]
        API_CLIENT["HTTP Client (Fetch / Axios)"]
        UI --> API_CLIENT
    end

    subgraph Server ["Backend Web Service (Render)"]
        FASTAPI["FastAPI App (uvicorn)"]
        MIDDLEWARE["Cors & Request Logging Middleware"]
        ROUTER["REST API Routes (/api/interview)"]
        SERVICE["Interview Service Layer"]
        AI_FACADE["AI Provider Facade"]
        REPO["Interview Repository (SQLAlchemy)"]

        FASTAPI --> MIDDLEWARE
        MIDDLEWARE --> ROUTER
        ROUTER --> SERVICE
        SERVICE --> REPO
        SERVICE --> AI_FACADE
    end

    subgraph AI_Engine ["AI Engine (backend/ai_engine)"]
        LANGGRAPH["LangGraph State Graph"]
        CHAINS["Evaluation & RAG Chains"]
        GEMINI_MODEL["ChatGoogleGenerativeAI"]

        AI_FACADE --> LANGGRAPH
        LANGGRAPH --> CHAINS
        CHAINS --> GEMINI_MODEL
    end

    subgraph Data ["Cloud Infrastructure"]
        SUPABASE[("Supabase PostgreSQL DB")]
        GEMINI_API["Google Gemini API"]

        REPO -->|AsyncPG| SUPABASE
        GEMINI_MODEL -->|HTTPS| GEMINI_API
    end

    API_CLIENT -->|REST API| FASTAPI
```

---

## 4. Technology Stack

- **Frontend**: React 18, Vite, TypeScript, TailwindCSS, Lucide Icons
- **Backend**: Python 3.12, FastAPI, Uvicorn, Pydantic v2
- **Database**: PostgreSQL (Supabase), SQLAlchemy 2.0 (AsyncIO), AsyncPG, Alembic
- **AI Engine**: LangGraph, LangChain Core, LangChain Google GenAI, Google Gemini 2.0 Flash
- **Deployment**: Vercel (Frontend SPA), Render (Backend Web Service), Supabase (Database)

---

## 5. Directory Structure

```
project/
├── backend/
│   ├── ai_engine/               # AI Engine (Graphs, Chains, Prompts, Models)
│   │   ├── chains/              # LangChain output parser & evaluation chains
│   │   ├── graphs/              # LangGraph state machine & nodes
│   │   ├── models/              # Gemini Chat LLM initialization
│   │   ├── prompts/             # System prompt templates
│   │   ├── services/            # Interview & Evaluation AI Services
│   │   ├── utils/               # AI Helper utilities
│   │   └── vectorstores/        # Supabase pgvector retriever
│   ├── alembic/                 # Alembic database migrations
│   │   └── versions/            # Schema version migrations
│   ├── app/                     # FastAPI Application Layer
│   │   ├── api/routes/          # Health & Interview API routers
│   │   ├── core/                # Config, database, logging, middleware
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── providers/           # AI Provider Facade
│   │   ├── repositories/        # Database CRUD Repositories
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Business logic orchestration
│   │   └── utils/               # Response formatters
│   ├── tests/                   # Pytest test suite
│   ├── main.py                  # FastAPI Application Entry Point
│   ├── requirements.txt         # Backend Python Dependencies
│   └── .env.example             # Backend Environment Template
│
├── frontend/
│   ├── src/                     # React application source code
│   ├── package.json             # Frontend NPM Dependencies
│   ├── vite.config.ts           # Vite Build Configuration
│   ├── vercel.json              # Vercel SPA Routing Rewrites
│   └── .env.example             # Frontend Environment Template
│
├── README.md                    # Project Overview & Architecture
├── RUN_PROJECT.md               # Local Setup & Developer Guide
├── DEPLOYMENT.md                # Vercel, Render & Supabase Deployment Guide
└── .gitignore                   # Git Ignore Configuration
```

---

## 6. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 7. Frontend Setup

```bash
cd frontend

# Install node dependencies
npm install
```

---

## 8. Environment Variables

### Backend (`backend/.env`)
```env
DATABASE_URL=postgresql://postgres.your_ref:password%40@aws-1-ap-south-1.pooler.supabase.com:5432/postgres
DIRECT_URL=postgresql://postgres.your_ref:password%40@aws-1-ap-south-1.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://your_ref.supabase.co
SUPABASE_PUBLISHABLE_KEY=your_key
SUPABASE_SECRET_KEY=your_secret
GEMINI_API_KEY=your_gemini_key
HOST=0.0.0.0
PORT=8000
DEBUG=true
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### Frontend (`frontend/.env`)
```env
VITE_API_URL=http://localhost:8000
```

---

## 9. Database Setup

Apply database schema migrations to Supabase:

```bash
cd backend
alembic upgrade head
```

---

## 10. Running the Project

### Start Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Start Frontend
```bash
cd frontend
npm run dev
```

Visit the application at: `http://localhost:5173`

---

## 11. API Documentation

Interactive OpenAPI documentation is generated automatically:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Core API Endpoints
- `GET /api/health` — Health check status (DB + AI Provider)
- `POST /api/interview/start` — Initiate new interview session
- `POST /api/interview/answer` — Submit answer & receive evaluation
- `GET /api/interview/{id}` — Retrieve current interview status
- `GET /api/interview/{id}/history` — Retrieve full Q&A transcript
- `POST /api/interview/{id}/end` — Conclude interview session

---

## 12. Deployment Overview

- **Frontend**: Deployed as a static Single Page Application to **Vercel**.
- **Backend**: Deployed as an async Python Web Service to **Render**.
- **Database**: Managed PostgreSQL instance hosted on **Supabase**.

For step-by-step deployment instructions, refer to **[DEPLOYMENT.md](DEPLOYMENT.md)**.
