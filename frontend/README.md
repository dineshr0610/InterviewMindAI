# InterviewMind AI — Frontend

A modern, production-ready React 18 + TypeScript frontend for the **InterviewMind AI** platform built with Vite, Tailwind CSS, and Lucide icons.

---

## Core Features

- **Candidate Onboarding**: Configure candidate name, job role, topic, and initial difficulty.
- **Interactive Interview Chat**: Real-time Q&A interface displaying AI-generated questions and evaluations.
- **Live Evaluation Dashboard**: Visual score display (1-10), structured feedback, strengths, and areas for improvement.
- **Full Q&A Transcript History**: Complete timeline of past interview questions and answers.
- **Responsive Dark Theme**: Glassmorphism SaaS aesthetic optimized for desktop, tablet, and mobile browsers.

---

## Tech Stack

- **React 18** — User Interface library
- **TypeScript** — Static typing and type safety
- **Vite** — Lightning-fast development server & production bundler
- **Tailwind CSS** — Utility-first styling
- **React Router** — SPA routing
- **Lucide React** — UI icons

---

## Quick Start

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

Create `.env` in `frontend/`:
```env
VITE_API_URL=http://localhost:8000
```

### 3. Start Development Server
```bash
npm run dev
```

The application will run at: **`http://localhost:5173`**

### 4. Build for Production
```bash
npm run build
```

---

## Directory Structure

```text
frontend/
├── src/
│   ├── components/            # React UI & Interview Components
│   │   ├── common/            # Toast, Spinner, Status indicators
│   │   ├── interview/         # QuestionCard, AnswerBox, EvaluationPanel
│   │   └── layout/            # Header, Navbar, Footer
│   ├── pages/                 # Page components (Home, Interview, NotFound)
│   ├── router/                # React Router configuration
│   ├── services/              # API Client & Interview API Service
│   ├── types/                 # TypeScript interfaces
│   ├── utils/                 # Classname & text parsing helpers
│   ├── App.tsx                # Root Application Component
│   ├── index.css              # Global styles & Tailwind directives
│   └── main.tsx               # Client Entry Point
├── package.json               # NPM Dependencies & Scripts
├── tsconfig.json              # TypeScript Compiler Config
├── vite.config.ts             # Vite Configuration
├── vercel.json                # Vercel SPA Routing Rewrite Rules
└── .env.example               # Environment Variables Template
```

---

## API Integration

The frontend connects to the FastAPI backend running at `http://localhost:8000` via the following REST endpoints:

- `GET /api/health` — Check backend health & DB connection status
- `POST /api/interview/start` — Initiate a new interview session
- `POST /api/interview/answer` — Submit an answer for AI evaluation
- `GET /api/interview/:id` — Retrieve current interview state
- `GET /api/interview/:id/history` — Retrieve complete Q&A history transcript
- `POST /api/interview/:id/end` — Conclude active interview session

---

## Vercel Deployment

Deployment configuration is defined in `vercel.json` for SPA routing:
```json
{
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

Set the production environment variable on Vercel Dashboard:
- `VITE_API_URL` = `https://your-backend.onrender.com`
