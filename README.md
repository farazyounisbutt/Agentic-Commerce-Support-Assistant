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

`DATABASE_URL` uses SQLAlchemy's psycopg 3 dialect. Its default value targets the Compose database exposed on port 5433.

## Run PostgreSQL

```bash
docker compose up -d postgres
```

The container uses the pgvector image. Database data persists in the `postgres_data` Docker volume.

## Start the API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

The health endpoint is available at `http://localhost:8000/api/health`.

## Run database migrations

With PostgreSQL running and `DATABASE_URL` configured:

```bash
cd apps/api
alembic upgrade head
```

To revert the initial commerce schema migration:

```bash
alembic downgrade base
```

## Seed demo data

After migrations, replace local commerce records with the deterministic demo dataset:

```bash
cd apps/api
python -m app.db.seed --reset
```

## Ingest support knowledge

Set `OPENAI_API_KEY` in `.env`; the default embedding model is `text-embedding-3-small` with its 1,536-dimension vector schema. Then ingest the three Markdown policy/FAQ documents:

```bash
cd apps/api
python -m app.ai.retrieval.ingest --reset
```

The ingestion command reads `data/knowledge`, creates OpenAI embeddings, and stores them in PostgreSQL + pgvector. It does not generate customer-facing answers.

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

Completed: repository layout, API health endpoint, settings, Compose PostgreSQL with pgvector, frontend shell, commerce seed data, and the RAG data/retrieval foundation.

Not implemented: LangGraph workflow, order/product tools, chat, approvals, authentication, or integrations.
