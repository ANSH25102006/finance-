# Personal Finance Spend Auditor

A production-ready, security-hardened personal finance auditing platform built with FastAPI, PostgreSQL, and React. The application provides deterministic financial intelligence, bank statement processing (CSV & PDF), merchant normalization, recurring detection, predictive forecasts, budget recommendations, and investment compounding simulations.

---

## Architecture Overview

- **Frontend**: Single Page Application built with **React**, **Vite**, **TypeScript**, **Tailwind CSS**, and **Lucide Icons**. SPA client-side routing with Vercel deployment support (`vercel.json`).
- **Backend**: Deterministic RESTful web services powered by **FastAPI** and **SQLAlchemy ORM**. Features 14 rule detectors, linear trend forecasting, rolling category budget recommendations, and instant multi-format statement parsing.
- **Database**: PostgreSQL (Render, Railway, Supabase, Neon) with Alembic migration version control. Supports automatic conversion of `postgres://` environment variables.

---

## Getting Started

### 1. Requirements

- Python 3.10+
- Node.js 18+
- PostgreSQL database (or SQLite fallback for local dev)

### 2. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment template and set your configuration:
   ```bash
   cp .env.example .env
   ```
5. Apply database migrations:
   ```bash
   alembic upgrade head
   ```
6. Start local dev server:
   ```bash
   uvicorn app.main:app --reload
   ```
   *Swagger documentation: http://localhost:8000/docs*

### 3. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start Vite dev server:
   ```bash
   npm run dev
   ```
   *Client application: http://localhost:5173*

---

## Production Deployment Guide

### Backend (Render / Railway)
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Migration Command**: `alembic upgrade head`
- **Required Environment Variables**:
  - `DATABASE_URL`: Hosted PostgreSQL connection string.
  - `SECRET_KEY`: Random 64-character hex key (`python -c "import secrets; print(secrets.token_hex(32))"`).
  - `CORS_ORIGINS`: Comma-separated allowed frontend domain(s) (e.g. `https://your-app.vercel.app`).
  - `DEBUG`: Set to `False` in production.

### Frontend (Vercel)
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Required Environment Variables**:
  - `VITE_API_BASE_URL`: Your deployed backend production URL (e.g. `https://your-backend.onrender.com`).

---

## Testing & Quality Assurance

Run complete backend test suite:
```bash
cd backend
source venv/bin/activate
pytest -q
```

Run frontend production build:
```bash
cd frontend
npm run build
```