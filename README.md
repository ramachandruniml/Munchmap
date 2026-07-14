# Munchmap

AI-powered, constraint-based meal planning for college students. Given a budget, dietary
restrictions, dorm equipment, and campus dining menus, Munchmap generates an optimized weekly
meal plan that minimizes cost and ingredient waste while hitting nutrition targets.

## Architecture

| Layer | Tech |
| --- | --- |
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Backend API | FastAPI (async) |
| Optimization engine | Google OR-Tools (LP/CP) |
| ML | sentence-transformers (recipe/ingredient embeddings), Claude API (menu parsing) |
| Queue | Redpanda (Kafka-compatible) |
| Cache | Redis |
| Database | PostgreSQL + pgvector |
| Workers | Arq |
| Observability | Prometheus + Grafana |
| CI/CD | GitHub Actions |

## Getting started

### Local development (no Docker)

Backend:

```bash
cd backend
py -3.12 -m venv .venv
./.venv/Scripts/activate   # .venv/bin/activate on macOS/Linux
pip install -r requirements-dev.txt
cp ../.env.example ../.env
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

### Full stack via Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

This starts Postgres (with pgvector), Redis, Redpanda, the FastAPI backend, an Arq worker, and
the Next.js frontend.

## Project layout

```
backend/    FastAPI app, optimization engine, workers, tests
frontend/   Next.js app (App Router) + shadcn/ui components
.github/    CI workflows
```
