# Architecture Overview

## System Overview

The application uses a lightweight web frontend, API backend, LangGraph orchestration layer, and a single PostgreSQL database.

High-level architecture:

```text
Customer / Reviewer
       |
       v
Next.js Web Application
       |
       v
FastAPI Backend
       |
       v
LangGraph Workflow
       |
       +-----------------------------+
       |             |               |
       v             v               v
   RAG Retrieval   Order Tool    Product Tool
       |             |               |
       +-------------+---------------+
                     |
                     v
               Response Generation
                     |
                     v
              Evidence/Risk Check
                     |
              +------+------+
              |             |
              v             v
            Safe       Human Review
              |             |
              |        LangGraph Pause
              |             |
              +------+------+
                     |
                     v
                Final Response
```

## Frontend

Technology:

- Next.js
- TypeScript
- Tailwind CSS

Primary UI areas:

### Customer Chat

Used to demonstrate customer interaction with the AI assistant.

### Agent Trace / Review

Used to expose structured execution information such as:

- intent
- graph path
- retrieval activity
- tool calls
- risk/evidence decisions
- escalation state
- execution timing

The trace interface must not expose model chain-of-thought.

## Backend

Technology:

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2
- Alembic
- psycopg 3

The backend owns:

- HTTP APIs
- application configuration
- database access
- domain services
- AI orchestration integration
- trace persistence
- human-review APIs

## Agent Orchestration

LangGraph is responsible for:

- graph state
- routing
- workflow execution
- conditional transitions
- human-review interrupts
- graph resume behavior
- persisted workflow state

LangChain is used where useful for:

- model integration
- embeddings
- document handling
- retrieval integration
- tool integration

Do not force every application component through LangChain abstractions.

## Structured Business Tools

Order and product information must be accessed through typed application tools.

Examples:

- `lookup_order`
- `search_products`
- `get_product`

These tools should call application services and parameterized database queries.

Do not give the LLM unrestricted SQL access.

## Database

Use one PostgreSQL database for MVP infrastructure.

The database will eventually contain:

### Commerce Data

- customers
- products
- product variants
- orders
- order items
- shipments

### RAG Data

- knowledge documents
- knowledge chunks
- embeddings

### AI Runtime Data

- conversations
- messages
- agent runs
- agent run events
- escalations
- graph/checkpoint state where appropriate

## Vector Search

Use pgvector inside PostgreSQL.

Reasons:

- minimal infrastructure
- sufficient for MVP scale
- keeps structured and vector data together
- simple local reproducibility
- strong portfolio demonstration

Do not add a separate vector database unless a future requirement materially justifies it.

## Human-in-the-Loop

Sensitive requests should route to a human-review state.

The workflow should use LangGraph interrupt/resume behavior.

The reviewer may:

- approve
- reject
- edit and approve

The MVP does not execute real refunds or payments.

## Safety / Grounding Strategy

Do not rely only on a model-provided numeric confidence score.

Prefer observable evidence signals such as:

- whether relevant RAG documents were retrieved
- whether an order exists
- whether a product/variant exists
- whether a request requires a policy exception
- whether a tool failed
- whether the requested information is supported

Unsupported answers should fall back safely rather than hallucinate.

## Infrastructure

Use Docker Compose for PostgreSQL + pgvector.

Do not add unnecessary infrastructure such as:

- Redis
- Kafka
- Kubernetes
- external vector stores

The architecture should remain compact and easy to run locally.

