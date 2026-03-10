# Wool Stash Tracker

A locally-hosted web app for cataloguing a personal wool/yarn stash.

## Tech Stack

- **Backend:** Python 3.11+ / FastAPI / SQLAlchemy 2.x / Alembic / Pydantic v2
- **Frontend:** React 18 / TypeScript / Vite / shadcn/ui / Tailwind CSS v4 / TanStack Query v5
- **Database:** SQLite (in `data/wool.db`)
- **Deployment:** Docker Compose on port 8001

## Local Development

### Backend
```bash
cd backend
source .venv/bin/activate
uvicorn backend.main:app --reload
```
Runs on http://localhost:8000

### Frontend
```bash
cd frontend
npm run dev
```
Runs on http://localhost:5173, proxies /api to backend

### Tests
```bash
# Backend
backend/.venv/bin/python -m pytest backend/tests/ -v

# Frontend
cd frontend && npm test
```

## Key Conventions

- **British English** throughout: "colour", "metres", "fibre", "catalogue"
- **TDD** for backend: write failing test → implement → verify
- **Schema changes** go through Alembic: update models.py → `alembic revision --autogenerate` → update schemas.py → update types.ts
- **Route order matters** in `backend/routers/yarns.py`: fixed-path routes before `/{yarn_id}`
- **Computed fields:** `estimated_total_metres` is calculated server-side on every create/update

## Deployment

```bash
# First deploy
git clone <repo> wool && cd wool
mkdir -p data
docker compose up --build -d
docker compose exec -w /app/backend wool alembic upgrade head
curl -X POST http://localhost:8001/api/yarns/seed

# Updates
git pull && docker compose up --build -d
docker compose exec -w /app/backend wool alembic upgrade head
```

## Project Structure

- `backend/` — FastAPI app, models, schemas, routers, tests, Alembic
- `frontend/` — React app, components, hooks, API client
- `data/` — SQLite database (gitignored, persisted via Docker volume)
- `docs/` — Design specs and implementation plans
