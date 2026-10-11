# Agentic Commerce Support Assistant

A compact, portfolio-grade AI support demo for the fictional **Northstar Outfitters** store. It combines evidence-grounded policy answers, typed commerce lookups, LangGraph routing, and real human review pauses—without pretending to be a full e-commerce platform.

## What it demonstrates

- Grounded policy and FAQ answers from PostgreSQL + pgvector retrieval.
- Deterministic product and order lookup through typed application tools, never LLM-generated SQL.
- A LangGraph workflow that routes knowledge, product, order, fallback, and sensitive requests.
- A cosine-distance relevance gate (`0.70`) that refuses to ground unrelated retrieval results.
- Real LangGraph interrupt/resume human review for refund, damaged-item, and exception requests.
- A minimal responsive chat UI with a structured Agent Trace: intent, graph path, tool results, evidence, risk flags, and escalation state.
- Deterministic fictional catalog, customer, order, shipment, and policy data for repeatable demos.

## Demo scenarios

1. **Policy:** “How many days do I have to return an item?”
2. **Order:** “Where is order ORD-1007?”
3. **Product:** “Do you have Trail Runner shoes in size 10?”
4. **Unsupported claim:** “Does every product have a lifetime warranty?”
5. **Human review:** “My order arrived damaged. Refund it.” Then approve, edit, or reject the proposed response.

## Architecture

```text
Browser (Next.js + Tailwind)
  |  POST /api/chat, POST /api/chat/{conversation_id}/resume
  v
FastAPI
  v
LangGraph support workflow
  |-- knowledge -> pgvector retrieval -> relevance gate (distance <= 0.70)
  |-- order -----> typed order service ------> PostgreSQL
  |-- product ---> typed product service ----> PostgreSQL
  `-- sensitive -> interrupt -> reviewer decision -> resume
  v
Structured response + safe Agent Trace (no chain-of-thought)
```

## Tech stack

- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS
- Backend: FastAPI, Pydantic, SQLAlchemy 2, Alembic, psycopg 3
- AI: LangGraph, LangChain, OpenAI chat and embedding integrations
- Data: PostgreSQL 16 with pgvector, Docker Compose
- Tests: pytest with deterministic/mocked AI dependencies

## Local setup

Prerequisites: Python 3.12+, Node.js 20.9+, and Docker Compose.

1. Create local environment configuration. Do not commit this file.

   ```bash
   cp .env.example .env
   ```

   Set the placeholders as needed:

   ```dotenv
   POSTGRES_PASSWORD=replace-with-a-local-password
   DATABASE_URL=postgresql+psycopg://agentic_commerce:replace-with-a-local-password@localhost:5433/agentic_commerce_support
   OPENAI_API_KEY=your-openai-api-key
   OPENAI_CHAT_MODEL=gpt-4.1-mini
   OPENAI_EMBEDDING_MODEL=text-embedding-3-small
   OPENAI_EMBEDDING_DIMENSIONS=1536
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

2. Start PostgreSQL + pgvector. The host port is **5433**.

   ```bash
   docker compose up -d postgres
   ```

3. Install the API and prepare deterministic data.

   ```bash
   cd apps/api
   python -m venv .venv
   source .venv/bin/activate
   pip install -e '.[dev]'
   alembic upgrade head
   python -m app.db.seed --reset
   python -m app.ai.retrieval.ingest --reset
   ```

   Knowledge ingestion and live chat require `OPENAI_API_KEY`. Unit tests do not.

4. Start the API in one terminal.

   ```bash
   cd apps/api
   source .venv/bin/activate
   uvicorn app.main:app --reload
   ```

5. Start the web app in another terminal, then open `http://localhost:3000`.

   ```bash
   cd apps/web
   npm install
   npm run dev
   ```

The API health endpoint is `http://localhost:8000/api/health`.

## Tests and checks

```bash
cd apps/api && pytest -q
cd apps/api && python -m compileall -q app
cd apps/web && npm run type-check
cd apps/web && npm run lint
cd apps/web && npm run build
git diff --check
```

## Safety and scope

The assistant only reads seeded commerce data and approved knowledge documents. It does not expose unrestricted SQL, execute refunds or payments, mutate inventory, connect to Shopify, or expose private model reasoning. Weak or missing retrieval evidence yields a safe unverifiable response, and sensitive requests pause for a human reviewer.

`InMemorySaver` intentionally keeps review checkpoints process-local for this MVP. Restarting the API clears in-flight review threads.

## Possible next enhancements

- Durable checkpoint and trace storage for multi-process deployments.
- Authenticated reviewer access and a small review queue.
- Evaluation fixtures and production observability around retrieval quality.
