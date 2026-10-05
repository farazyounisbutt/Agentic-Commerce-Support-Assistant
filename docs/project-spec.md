# Agentic Commerce Support Assistant - Project Spec

## Objective

Build a compact, portfolio-grade Agentic E-commerce Support Assistant MVP that demonstrates practical implementation of:

- AI agents
- RAG
- LangChain
- LangGraph
- embeddings and vector search
- PostgreSQL + pgvector
- tool calling
- structured business-data retrieval
- human-in-the-loop workflows
- production-oriented AI architecture

The goal is not to build a full e-commerce platform.

The project should be small enough to complete relatively quickly, while still demonstrating meaningful technical depth suitable for:

- GitHub
- Upwork portfolio
- InLoop Technologies case study
- technical interviews
- client proposals

## Product Concept

A customer interacts with an AI support assistant through a simple chat interface.

The assistant determines the type of request and routes it through the appropriate workflow.

High-level flow:

Customer Query  
→ Intent / Routing  
→ Knowledge RAG OR Order Tool OR Product Tool  
→ Response Generation  
→ Evidence / Risk Evaluation  
→ Human Escalation when required  
→ Final Response

## MVP Capabilities

### 1. Store Knowledge RAG

Support questions based on small store-support documents such as:

- shipping policy
- returns/refunds policy
- FAQ
- other small support documents if needed

Responses should be grounded in retrieved documents and expose useful source references.

### 2. Order Lookup

Support structured retrieval of seeded order information including:

- order status
- shipping status
- tracking information
- basic order details

Order lookup must use typed application tools and normal database access.

Do not use free-form LLM-generated SQL.

### 3. Product Lookup

Support structured retrieval of seeded product information including:

- product details
- product variants
- availability
- stock information
- size/color where relevant

Product lookup must use typed application tools.

### 4. Human-in-the-Loop

Sensitive or high-risk requests must not be automatically executed.

Examples:

- refund requests
- policy exceptions
- unusual complaints
- requests requiring human judgment

LangGraph should route these cases to a human-review state.

The graph should actually pause and later resume after the review decision.

The MVP will not process real refunds or payments.

Human approval applies to the proposed support resolution/response.

## Customer UI

The customer-facing interface should remain minimal and polished.

It should show:

- customer messages
- assistant responses
- source references where useful
- escalation/review status where relevant

## Agent Trace UI

A lightweight technical trace screen should make the AI architecture visible during demonstrations.

Useful information includes:

- detected intent
- selected graph node/path
- selected tool
- tool arguments
- structured tool result summary
- retrieved documents
- evidence status
- risk flags
- escalation decision
- node execution timing
- final run status

Do not expose private model chain-of-thought.

Expose structured execution metadata only.

## Seed Data

Use realistic fictional data for a single demo store.

Initial target:

- approximately 10–20 products
- approximately 10–20 orders
- several customers
- shipping policy
- returns/refunds policy
- FAQ

No real customer, payment, or personal data is required.

## Technology Direction

Preferred stack:

- Next.js
- TypeScript
- Tailwind CSS
- FastAPI
- Python
- LangGraph
- LangChain
- PostgreSQL
- pgvector
- OpenAI initially
- Docker Compose

Keep the LLM/provider configuration environment-driven where practical.

## Explicitly Out of Scope

Do not implement in the initial MVP unless separately approved:

- full Shopify integration
- real refund processing
- payments
- carts
- CRM
- email support
- omnichannel support
- multi-tenant SaaS architecture
- advanced analytics
- complex authentication/authorization
- production billing
- Shopify App Store packaging
- large admin dashboard
- Redis
- Kafka
- Kubernetes
- separate vector databases such as Pinecone or Qdrant

## Engineering Principles

The MVP should demonstrate:

- clear module boundaries
- typed interfaces
- structured agent state
- deterministic business tools
- sensible error handling
- useful tests
- reproducible setup
- migrations
- seeded demo data
- observable graph execution
- documented architecture

Prioritize AI workflow depth over feature breadth.

## Completion Criteria

The MVP should support these demonstration scenarios:

### Policy RAG

Customer asks:

“How many days do I have to return an item?”

The system retrieves the relevant policy and returns a grounded response with source information.

### Order Lookup

Customer asks:

“Where is order ORD-1007?”

The system retrieves structured order and shipment information.

### Product Lookup

Customer asks:

“Do you have Trail Runner shoes in size 10?”

The system retrieves structured catalog/variant data.

### Unsupported Claim

Customer asks for information that is not supported by available policy or product data.

The assistant must not invent an answer.

### Human Escalation

Customer requests a refund or policy exception.

The LangGraph workflow pauses for human review.

### Resume

A human reviewer approves, rejects, or edits the proposed response.

The same workflow thread resumes and completes.

