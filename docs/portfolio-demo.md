# Portfolio Demo Guide

Agentic Commerce Support Assistant is a compact full-stack demonstration of an evidence-first customer-support workflow for the fictional Northstar Outfitters store. It combines a Next.js customer experience with FastAPI, typed SQLAlchemy commerce services, PostgreSQL + pgvector, LangChain integrations, and LangGraph orchestration.

The project is intentionally narrow: it shows the decisions that make an AI support feature safe and inspectable instead of attempting to model an entire commerce platform. Product and order data is fetched through typed tools, policy answers require relevant retrieval evidence, and sensitive requests interrupt for a human decision. No real customer data, refunds, payments, or private chain-of-thought are used or exposed.

## Capabilities to highlight

- Grounded policy and FAQ answers with source distance in the trace
- Structured order and product lookup from deterministic fictional data
- Relevance gating that safely declines unsupported warranty claims
- LangGraph human-review interrupt, approve, edit, reject, and resume flow
- Responsive chat UI plus a reviewer-facing Agent Trace

## Recommended four-flow demo

1. Ask: **“How many days do I have to return an item?”** Show the source and `GROUNDED` evidence status.
2. Ask: **“Where is order ORD-1007?”** Show the shipped status, carrier, tracking, and typed order result.
3. Ask: **“Does every product have a lifetime warranty?”** Show that distant RAG chunks remain visible but the response is marked `INSUFFICIENT_EVIDENCE`.
4. Ask: **“My order arrived damaged. Refund it.”** Show the interruption, review payload, and an EDIT decision completing with the reviewer’s text.

## Screenshots to capture

1. Landing state with the four demo prompt chips and fictional-store note.
2. Policy answer with Agent Trace sources, evidence status, and graph path.
3. `ORD-1007` result with shipment information and typed tool-result summary.
4. Human-review card showing escalation reason, customer request, proposed response, risk, and action controls.
5. Post-resume state after an edited response completes.

## Portfolio headline

**Built an evidence-first agentic commerce support assistant with LangGraph HITL, pgvector RAG, and typed business-data tools.**

## Portfolio description

I built a portfolio-grade commerce support MVP that demonstrates how to make AI support workflows useful without giving an LLM unrestricted data access or authority to take sensitive actions. The Next.js interface sends chat requests to a FastAPI backend, where a LangGraph workflow routes policy, order, product, fallback, and refund/exception requests. Policy answers are retrieved from PostgreSQL + pgvector and pass a deterministic cosine-distance relevance gate before being considered grounded. Order and catalog information comes from typed SQLAlchemy application services rather than generated SQL. Sensitive damaged-item and refund requests pause with LangGraph interrupt/resume for an explicit human approve, edit, or reject decision. A compact Agent Trace exposes intent, graph path, evidence, typed tool results, risk flags, and escalation state—while deliberately excluding private chain-of-thought. The demo uses repeatable fictional data and does not execute refunds or payments.
