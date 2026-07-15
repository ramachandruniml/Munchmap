# Munchmap

AI-powered, constraint-based meal planning for college students. Given a budget, dietary
restrictions, dorm equipment, and campus dining menus, Munchmap generates an optimized weekly
meal plan that minimizes cost and ingredient waste while hitting nutrition targets.

**Current status**: the core loop is implemented end-to-end - sign up, complete onboarding
(budget/diet/equipment), generate an OR-Tools-optimized weekly meal plan, and get a consolidated
grocery list. Dining-hall menu parsing, pantry tracking, recipe-discovery embeddings, feedback
learning, and the observability/dashboard layer are not built yet.

## Architecture

| Layer | Tech |
| --- | --- |
| Frontend | Next.js 16 (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Backend API | FastAPI (async) |
| Auth | Supabase Auth (backend verifies JWTs via Supabase's JWKS endpoint) |
| Optimization engine | Google OR-Tools CP-SAT |
| Database | PostgreSQL (hosted by Supabase) + pgvector (for future embeddings) |
| ML (planned) | sentence-transformers (recipe/ingredient embeddings), Claude API (menu parsing) |
| Queue (scaffolded, unused so far) | Redpanda (Kafka-compatible) |
| Cache | Redis |
| Workers | Arq |
| Observability (planned) | Prometheus + Grafana |
| CI/CD | GitHub Actions |

## Getting started

### 1. Create a Supabase project

Auth and Postgres are both hosted by Supabase (Supabase Auth owns `auth.users`; our tables live
in the same database's `public` schema).

1. Create a project at [supabase.com](https://supabase.com).
2. **Project Settings -> API**: copy the **Project URL** and **anon public key**.
3. **Project Settings -> Database -> Connection string**: copy the URI (pooled "Transaction"
   mode for the app; the direct connection also works for running migrations).

### 2. Configure environment variables

```bash
cp .env.example .env                       # backend + docker-compose
cp frontend/.env.local.example frontend/.env.local   # frontend (Next.js only reads its own dir)
```

Fill in `SUPABASE_URL`, `DATABASE_URL` in `.env`, and `NEXT_PUBLIC_SUPABASE_URL` /
`NEXT_PUBLIC_SUPABASE_ANON_KEY` in `frontend/.env.local`.

### 3. Backend

```bash
cd backend
py -3.12 -m venv .venv   # OR-Tools/sentence-transformers don't yet ship wheels for 3.14
./.venv/Scripts/activate   # .venv/bin/activate on macOS/Linux
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

To seed real recipe data: download `RAW_recipes.csv` from Kaggle's
[Food.com Recipes and Interactions](https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions)
dataset, place it at `backend/data/RAW_recipes.csv`, then run:

```bash
python -m scripts.seed_recipes
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Sign up at `/signup`, complete onboarding at `/onboarding`, then generate a plan at `/plan`.

### Full stack via Docker Compose

```bash
docker compose up --build
```

Starts Redis, Redpanda, the FastAPI backend, an Arq worker, and the Next.js frontend. Postgres
is not containerized here - it's the Supabase-hosted instance from step 1.

## Project layout

```
backend/    FastAPI app, OR-Tools optimizer, Alembic migrations, seed script, tests
frontend/   Next.js app (App Router), Supabase auth, shadcn/ui components
.github/    CI workflows
```
