# Backend (FastAPI) — Cosmetic P&D Suite (Phase 1)

Quick start (from workspace root):

1. Create a Python venv and install deps

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
python -m playwright install
```

2. Run the app

```bash
uvicorn backend.main:app --reload
```

Notes:
- This setup uses FastAPI + Playwright; no Docker/Redis required.
- Scrape jobs use FastAPI BackgroundTasks and persist results to `backend/data/results`.
- Supabase persistence is configured through the workspace `.env` file.
- If direct Postgres host access is blocked, provide `SUPABASE_SERVICE_ROLE_KEY` and use the Supabase dashboard SQL editor or CLI to deploy `schema.sql`.
