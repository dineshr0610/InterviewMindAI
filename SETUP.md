# InterviewMind AI - Environment Setup & Credential Guide

This guide explains how to acquire, configure, and verify all real environment credentials for **InterviewMind AI**.

---

## 1. Credentials & Configuration Overview

| Variable Name | Required / Optional | Description | Primary Usage File |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | **Mandatory** | Pooled PostgreSQL Connection string (Port 6543) | `backend/.env` |
| `DIRECT_URL` | **Mandatory** | Direct PostgreSQL Connection string (Port 5432) | `backend/.env` |
| `SUPABASE_URL` | **Mandatory** | Supabase Project API Endpoint URL | `backend/.env` |
| `SUPABASE_PUBLISHABLE_KEY` | Recommended | Supabase Public / Anon API Key | `backend/.env` |
| `SUPABASE_SECRET_KEY` | Recommended | Supabase Service Role / Secret API Key | `backend/.env` |
| `GEMINI_API_KEY` | **Mandatory** | Google Gemini Generative AI API Key | `backend/.env` |
| `VITE_API_URL` | **Mandatory** | FastAPI Backend Base URL (`http://localhost:8000`) | `frontend/.env` |

---

## 2. Where to Obtain Each Key

### A. Supabase Database & API Keys
1. Log in to [Supabase Console](https://supabase.com/dashboard).
2. Select your project (or create a new project).
3. Navigate to **Project Settings** → **Database**:
   - Scroll to **Connection Strings** → Select **Transaction Pooler (Port 6543)**. Copy string for `DATABASE_URL`.
   - Select **Session / Direct (Port 5432)**. Copy string for `DIRECT_URL`.
   - *Note*: Replace `[YOUR-PASSWORD]` in the connection string with your database password.
4. Navigate to **Project Settings** → **API**:
   - **Project URL**: Copy for `SUPABASE_URL`.
   - **anon / public key**: Copy for `SUPABASE_PUBLISHABLE_KEY`.
   - **service_role / secret key**: Copy for `SUPABASE_SECRET_KEY`.

### B. Google Gemini API Key
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Click **Create API Key**.
3. Copy the generated API key string for `GEMINI_API_KEY`.

---

## 3. Where to Paste Each Key

### File 1: `backend/.env`
Create `backend/.env` (or copy from `backend/.env.example`) and fill in:

```ini
# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
DIRECT_URL=postgresql+asyncpg://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres

# Supabase Project Credentials
SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
SUPABASE_PUBLISHABLE_KEY=your-actual-anon-key-here
SUPABASE_SECRET_KEY=your-actual-service-role-key-here

# AI Credentials
GEMINI_API_KEY=your-actual-gemini-api-key-here

# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=false
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:5174"]
```

### File 2: `frontend/.env`
Create `frontend/.env` (or copy from `frontend/.env.example`) and fill in:

```ini
VITE_API_URL=http://localhost:8000
```

---

## 4. Service Verification Checklist

### 1. Database Connection Verification
Run database migrations against Supabase:
```bash
cd backend
alembic upgrade head
```
*Expected Output*: Alembic creates `interviews` and `interview_messages` tables without error.

### 2. Backend Health API Verification
Start the backend server:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Open browser or run curl:
```bash
curl http://localhost:8000/api/health
```
*Expected Output*:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "database": "connected"
  }
}
```

### 3. Gemini AI Engine Verification
Start an interview session via Swagger docs (`http://localhost:8000/docs`) or frontend:
- Call `POST /api/interview/start` with payload:
  ```json
  {
    "candidate_name": "Test User",
    "role": "Frontend Engineer",
    "topic": "React Hooks"
  }
  ```
- *Expected Result*: Returns a live, dynamically generated question from Gemini AI.

### 4. End-to-End Frontend Verification
Launch the frontend:
```bash
cd frontend
npm run dev
```
Navigate to `http://localhost:5173` in your browser and complete a test interview session.
