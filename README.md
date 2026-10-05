# Agentic Commerce Support

An MVP foundation for an agentic e-commerce support assistant. This first task deliberately provides only the application scaffold; no product, order, AI, RAG, or chat functionality exists yet.

## Current architecture

- `apps/api`: FastAPI, SQLAlchemy 2, psycopg 3, Alembic, and pytest.
- `apps/web`: Next.js, TypeScript, and Tailwind CSS shell.
- PostgreSQL with pgvector through Docker Compose.
- `data`, `docs`, and `scripts`: reserved project-level directories.

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker with Docker Compose

## Local setup

Copy the example environment file and replace the database password if desired:

```bash
cp .env.example .env
```

`DATABASE_URL` uses SQLAlchemy's psycopg 3 dialect. Its default value targets the Compose database exposed on port 5432.

## Run PostgreSQL

```bash
docker compose up -d postgres
```

The container uses the pgvector image, so the `vector` extension is available for a future Alembic migration. Database data persists in the `postgres_data` Docker volume.

## Start the API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

The health endpoint is available at `http://localhost:8000/api/health`.

## Start the frontend

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000`.

## Run backend tests

```bash
cd apps/api
pytest
```

## Current status

Completed: repository layout, API health endpoint, settings, database/Alembic foundation, Compose PostgreSQL with pgvector, frontend shell, and API tests.

Not implemented: domain schema, seed data, RAG, embeddings, LangGraph workflow, tools, chat, approvals, authentication, or integrations.

