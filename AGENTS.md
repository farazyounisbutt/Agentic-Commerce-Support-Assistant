# AGENTS.md

## Project

Agentic Commerce Support Assistant

This repository is a compact, portfolio-grade MVP demonstrating:

- LangGraph
- LangChain
- RAG
- PostgreSQL + pgvector
- tool calling
- structured e-commerce data retrieval
- human-in-the-loop workflows
- observable agent execution

This is not intended to become a full e-commerce platform.

## Authoritative Documentation

Before making significant changes, read and follow:

- `docs/project-spec.md`
- `docs/architecture/overview.md`
- `docs/architecture/langgraph-workflow.md`
- `docs/implementation-status.md`

Treat these files as the current source of truth.

If implementation requirements conflict with the documentation, do not silently redesign the system. Report the conflict.

## General Development Rules

- Implement only the requested task.
- Do not start future milestones early.
- Prefer small, reviewable changes.
- Keep the architecture simple.
- Do not add infrastructure without a clear requirement.
- Avoid speculative abstractions.
- Prefer explicit typed interfaces.
- Preserve clear module boundaries.
- Use sensible error handling.
- Keep dependencies minimal.
- Do not commit secrets.
- Do not create Git commits or pull requests unless explicitly requested.

## Backend

Use:

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2
- psycopg 3
- Alembic

Guidelines:

- use modern Python typing
- use SQLAlchemy 2 typed `Mapped[...]` models
- keep database access in appropriate services/repositories
- use parameterized database access
- do not expose ORM models directly as API contracts
- use decimal/numeric database types for money
- use timezone-aware timestamps

## Frontend

Use:

- Next.js
- TypeScript
- Tailwind CSS

Guidelines:

- keep the UI minimal and polished
- do not introduce large UI frameworks without approval
- prefer reusable components where they materially help
- do not build features outside the current task

## AI Architecture

LangGraph owns workflow orchestration.

Use LangChain where useful for:

- model integration
- embeddings
- documents
- retrieval
- tool integration

Do not force all business logic through LangChain.

Structured commerce data must be accessed through typed tools such as:

- order lookup
- product lookup

Do not give the LLM unrestricted SQL access.

## RAG

Use PostgreSQL + pgvector.

Do not introduce external vector databases such as:

- Pinecone
- Qdrant
- Weaviate

unless explicitly approved.

RAG responses must be grounded in retrieved evidence.

Do not invent unsupported policy or product information.

## Human-in-the-Loop

Sensitive requests such as refunds or policy exceptions must route to human review.

Use real LangGraph interrupt/resume behavior.

The MVP must not execute real refunds, payments, or destructive commerce actions.

## Agent Trace

Expose structured execution metadata such as:

- detected intent
- graph node/path
- tool invocation
- retrieved sources
- evidence status
- risk flags
- escalation decision
- execution timing
- run status

Do not expose or attempt to persist private model chain-of-thought.

## Testing

For meaningful implementation changes:

- add or update relevant tests
- keep important logic deterministic where practical
- mock LLM calls in unit tests
- avoid requiring an OpenAI API key for the normal test suite
- avoid making the normal test suite depend unconditionally on Docker
- clearly mark integration tests that require PostgreSQL

Run the smallest relevant validation set before finishing.

## Documentation

Only update project documentation when:

- the task explicitly requires it, or
- an implementation decision materially changes documented architecture or project status

Do not rewrite project documentation unnecessarily.

## Scope Exclusions

Do not introduce unless explicitly approved:

- Shopify integration
- payment processing
- real refunds
- carts
- CRM
- email support
- omnichannel support
- multi-tenancy
- complex authentication
- billing
- Redis
- Kafka
- Kubernetes
- external vector databases
- large admin dashboards

## Completion Report

At the end of an implementation task, report only:

1. files or areas changed
2. important technical decisions
3. commands/tests executed
4. validation results
5. issues or decisions requiring review
6. suggested next task

Do not implement the suggested next task.
