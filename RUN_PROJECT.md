# RUN_PROJECT.md — Complete Local Execution & Troubleshooting Guide

This guide provides developer instructions to clone, set up, run, and verify **InterviewMind AI** from a fresh machine without manual debugging.

---

## 1. Prerequisites

Ensure your system has the following installed:

- **Python**: v3.10 to v3.12 (v3.12 verified)
- **Node.js**: v18.0.0+ (v20+ recommended)
- **npm**: v9+
- **Git**: Installed and available in terminal shell

---

## 2. Environment Setup

### 2.1 Clone Repository
```bash
git clone <your-repository-url>
cd interview
```

### 2.2 Backend Environment Setup

Navigate to `backend/` directory:
```bash
cd backend
```

Create Python Virtual Environment:
- **Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **Linux / macOS**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

Install all dependencies:
```bash
pip install -r requirements.txt
```

### 2.3 Frontend Environment Setup

Open a second terminal window and navigate to `frontend/`:
```bash
cd frontend
npm install
```

---

## 3. Environment Variables Configuration

### Backend Environment File (`backend/.env`)

Copy `backend/.env.example` to `backend/.env`:
```bash
cp .env.example .env
```

Populate the required credentials using placeholders below:
```env
DATABASE_URL=postgresql://postgres.[YOUR_PROJECT_REF]:[YOUR_ENCODED_PASSWORD]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres
DIRECT_URL=postgresql://postgres.[YOUR_PROJECT_REF]:[YOUR_ENCODED_PASSWORD]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres

SUPABASE_URL=https://[YOUR_PROJECT_REF].supabase.co
SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
SUPABASE_SECRET_KEY=your_supabase_secret_key

GEMINI_API_KEY=your_gemini_api_key

HOST=0.0.0.0
PORT=8000
DEBUG=true
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","http://localhost:3001"]
```

> **Important Note**: If your PostgreSQL password contains `@`, encode it as `%40` in the database URL strings.

### Frontend Environment File (`frontend/.env`)

Copy `frontend/.env.example` to `frontend/.env`:
```bash
cp .env.example .env
```

Set the API URL:
```env
VITE_API_URL=http://localhost:8000
```

---

## 4. Database Migrations (Supabase)

Run Alembic migrations to construct database tables:

```bash
cd backend
alembic upgrade head
```

### Expected Output
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> 001_initial_schema
```

---

## 5. Running the Application

### 1-Click Fast Launcher (Windows)
Double-click `start-all.bat` in the root `interview/` directory to launch both backend and frontend automatically!

### Manual Terminal Commands

#### 5.1 Start Backend FastAPI Server
```bash
cd backend
uvicorn main:app --reload --port 8000
```
- Server will run at: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`

#### 5.2 Start Frontend Vite Server
```bash
cd frontend
npm run dev
```
- App will run at: `http://localhost:5173`

---

## 6. Verification Steps

### 6.1 Run Backend Unit Tests
```bash
cd backend
pytest
```
*Expected Result*: `6 passed`

### 6.2 Test AI Engine & LangGraph Compilation
```bash
cd backend
python -c "from ai_engine.graphs.interview_graph import interview_graph; print('LangGraph compiled successfully:', interview_graph is not None)"
```
*Expected Result*: `LangGraph compiled successfully: True`

### 6.3 Test Full End-to-End API Workflow
```bash
python -c "import httpx; client = httpx.Client(timeout=30.0); r1 = client.get('http://localhost:8000/api/health'); print('Health:', r1.json()); r2 = client.post('http://localhost:8000/api/interview/start', json={'candidate_name': 'Tester', 'role': 'Engineer', 'topic': 'Python'}); print('Start:', r2.json()); i_id = r2.json()['data']['interview_id']; r3 = client.post('http://localhost:8000/api/interview/answer', json={'interview_id': i_id, 'answer': 'Python uses dynamic typing and automatic memory management.'}); print('Answer:', r3.json()); r4 = client.get(f'http://localhost:8000/api/interview/{i_id}/history'); print('History:', r4.json()); r5 = client.post(f'http://localhost:8000/api/interview/{i_id}/end'); print('End:', r5.json())"
```
*Expected Result*: All 5 API steps return `success: true`.

---

## 7. Common Errors and Troubleshooting

| Error | Cause | Resolution |
|---|---|---|
| `ModuleNotFoundError: No module named 'app'` or `'ai_engine'` | Python path missing backend folder | `backend/alembic/env.py` and `backend/app/providers/ai_provider.py` automatically add `backend` to `sys.path`. Ensure commands are run inside `backend/`. |
| `DuplicateObjectError: type "interview_status" already exists` | Enum type double creation in Alembic | Controlled via `postgresql.ENUM('...', create_type=False)`. |
| `TypeError: Object of type UUID / datetime is not JSON serializable` | Returning raw UUID/datetime in dict | Wrapped with `str()` and `.isoformat()` in `InterviewService`. |
| `socket.gaierror: getaddrinfo failed` | `@` character unencoded in DB password | Replace `@` with `%40` in `DATABASE_URL` and `DIRECT_URL`. |
| `WinError 121 / Semaphore timeout` | PgBouncer port 6543 connection issue | Use direct database connection port `5432`. |
| `UnicodeEncodeError: 'charmap'` | Windows console non-ASCII log symbols | Resolved by using ASCII log strings (`->`, `<-`, `[ERROR]`) in middleware. |
