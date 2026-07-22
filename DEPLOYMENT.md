# DEPLOYMENT.md — Production Deployment Guide

This document outlines the step-by-step procedure to deploy **InterviewMind AI** to production using:
- **Database**: Supabase (PostgreSQL + pgvector)
- **Backend Service**: Render (FastAPI + LangGraph AI Engine)
- **Frontend SPA**: Vercel (React + Vite + TypeScript)
- **AI Service**: Google Gemini API

---

## 1. Recommended Deployment Order

Follow this sequence to ensure zero-downtime integration:

```mermaid
flowchart LR
    Step1["1. Supabase Database"] --> Step2["2. Google Gemini API"]
    Step2 --> Step3["3. Render Backend"]
    Step3 --> Step4["4. Vercel Frontend"]
```

1. **Supabase Database**: Provision PostgreSQL instance and run Alembic migrations.
2. **Google Gemini API**: Generate production API key.
3. **Render Backend**: Deploy FastAPI web service configured with database & Gemini keys.
4. **Vercel Frontend**: Deploy Vite SPA pointing `VITE_API_URL` to Render backend URL.

---

## 2. Step 1: Database Setup (Supabase)

1. Sign in to [Supabase](https://supabase.com) and create a new project.
2. Go to **Project Settings > Database** to retrieve:
   - **Host**, **Database**, **Port (5432)**, **User**, and **Password**.
3. Formulate your connection strings:
   - `DATABASE_URL`: `postgresql://postgres.[REF]:[ENCODED_PASS]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres`
   - `DIRECT_URL`: `postgresql://postgres.[REF]:[ENCODED_PASS]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres`
   > *Note*: If your password contains `@`, encode it as `%40`.
4. Apply Alembic migrations from local terminal:
   ```bash
   cd backend
   # Ensure .env contains your Supabase DATABASE_URL
   alembic upgrade head
   ```

---

## 3. Step 2: AI Service (Google Gemini API)

1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Create a new API Key for model `gemini-2.0-flash`.
3. Save this key for configuring `GEMINI_API_KEY` on Render.

---

## 4. Step 3: Backend Deployment (Render)

1. Sign in to [Render](https://render.com) and click **New > Web Service**.
2. Connect your Git repository.
3. Configure the Web Service settings:
   - **Name**: `interviewmind-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Region**: Select region closest to Supabase (e.g., Singapore / Frankfurt)
   - **Branch**: `main`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
4. Set **Environment Variables** in Render Dashboard:
   | Variable Name | Value / Description |
   |---|---|
   | `DATABASE_URL` | Your Supabase connection string (Port 5432) |
   | `DIRECT_URL` | Your Supabase direct connection string |
   | `SUPABASE_URL` | `https://[YOUR_REF].supabase.co` |
   | `SUPABASE_PUBLISHABLE_KEY` | Your Supabase Publishable Key |
   | `SUPABASE_SECRET_KEY` | Your Supabase Secret Key |
   | `GEMINI_API_KEY` | Your Google Gemini API Key |
   | `HOST` | `0.0.0.0` |
   | `PORT` | `10000` (Render defaults to `$PORT`) |
   | `DEBUG` | `false` |
   | `CORS_ORIGINS` | `["https://your-app.vercel.app"]` |
5. Configure **Health Check Path**:
   - Health Check Path: `/api/health`
6. Deploy Web Service and copy your public service URL (e.g., `https://interviewmind-backend.onrender.com`).

---

## 5. Step 4: Frontend Deployment (Vercel)

1. Sign in to [Vercel](https://vercel.com) and click **Add New > Project**.
2. Import your Git repository.
3. Configure project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Set **Environment Variables**:
   | Variable Name | Value |
   |---|---|
   | `VITE_API_URL` | `https://interviewmind-backend.onrender.com` (Your Render URL) |
5. Click **Deploy**.
6. SPA routing rewrite rules are pre-configured in `frontend/vercel.json`:
   ```json
   {
     "framework": "vite",
     "rewrites": [
       { "source": "/(.*)", "destination": "/index.html" }
     ]
   }
   ```

---

## 6. Post-Deployment Verification Checklist

- [ ] **Health Endpoint**: `https://interviewmind-backend.onrender.com/api/health` returns `{"status": "healthy"}`
- [ ] **Swagger Documentation**: `https://interviewmind-backend.onrender.com/docs` loads OpenAPI interface
- [ ] **Frontend Application**: `https://your-app.vercel.app` loads React UI cleanly
- [ ] **CORS**: Verify no CORS errors appear in browser developer console
- [ ] **Database Persistence**: Verify interview sessions create records in Supabase `interviews` table
- [ ] **AI Responses**: Verify live Gemini AI responses are returned during interview sessions
