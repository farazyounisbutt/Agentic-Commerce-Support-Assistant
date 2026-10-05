# LangGraph Workflow

## Purpose

LangGraph is the primary orchestration layer for the AI support workflow.

The graph should make routing, tool usage, evidence checks, and human review explicit.

## Initial Workflow

```text
START
  |
  v
prepare_context
  |
  v
classify_intent
  |
  +------------------ knowledge ------------------> retrieve_knowledge
  |
  +------------------ order ----------------------> lookup_order
  |
  +------------------ product --------------------> lookup_product
  |
  +------------------ sensitive ------------------> prepare_escalation
  |
  +------------------ unknown --------------------> fallback

retrieval/tool result
  |
  v
generate_response
  |
  v
evaluate_response
  |
  +---------------- safe / grounded --------------+
  |                                               |
  +---------------- insufficient evidence ------> fallback
  |
  +---------------- sensitive ------------------> human_review
                                                  |
                                                  v
                                             INTERRUPT
                                                  |
                                       +----------+----------+
                                       |          |          |
                                       v          v          v
                                    approve      edit       reject
                                       |          |          |
                                       +----------+----------+
                                                  |
                                                  v
                                               finalize
                                                  |
                                                  v
                                                 END
```

## Initial Intent Types

Use a small explicit set of intents:

- KNOWLEDGE
- ORDER_LOOKUP
- PRODUCT_LOOKUP
- REFUND_OR_EXCEPTION
- GENERAL_SUPPORT
- UNKNOWN

The router should return structured data.

Conceptual example:

```json
{
  "intent": "ORDER_LOOKUP",
  "entities": {
    "order_number": "ORD-1007"
  },
  "requires_human_review": false
}
```

## Graph State

Graph state should remain explicit and typed.

Conceptual structure:

```python
class SupportState(TypedDict):
    conversation_id: str
    run_id: str

    user_message: str

    intent: str | None
    entities: dict

    retrieved_documents: list
    tool_calls: list
    tool_results: list

    draft_response: str | None

    risk_flags: list[str]
    evidence_status: str | None

    escalation_required: bool
    escalation_reason: str | None

    human_decision: dict | None

    final_response: str | None
```

The exact implementation can evolve during development.

## RAG Route

Typical path:

```text
classify_intent
      |
      v
retrieve_knowledge
      |
      v
generate_response
      |
      v
evaluate_response
```

Retrieved policy/FAQ evidence should be attached to the graph state and later exposed as sources.

## Order Route

Typical path:

```text
classify_intent
      |
      v
lookup_order
      |
      v
generate_response
      |
      v
evaluate_response
```

Order data should come from a typed application tool.

## Product Route

Typical path:

```text
classify_intent
      |
      v
lookup_product
      |
      v
generate_response
      |
      v
evaluate_response
```

Product/variant data should come from structured database access through a typed tool.

## Human Review Route

Sensitive requests should not complete automatically.

Example:

```text
Customer asks for refund
      |
      v
REFUND_OR_EXCEPTION
      |
      v
prepare_escalation
      |
      v
human_review
      |
      v
LangGraph interrupt
```

A reviewer can later:

- approve the suggested response
- modify and approve the response
- reject the suggested resolution

The graph should resume using the same persisted thread/workflow context.

## Evidence and Risk Evaluation

The evaluation node should use concrete signals where possible.

Examples:

- relevant knowledge retrieved
- order found/not found
- product found/not found
- policy exception detected
- refund request detected
- tool failure
- unsupported request

Do not use an arbitrary self-reported LLM confidence score as the sole decision mechanism.

## Observability

Each meaningful node execution should generate structured trace information suitable for the Agent Trace UI.

Useful fields include:

- run ID
- graph node
- event type
- selected intent
- selected tool
- tool result summary
- retrieved document references
- risk flags
- evidence status
- escalation state
- execution duration
- final run state

Do not persist or expose private model chain-of-thought.

