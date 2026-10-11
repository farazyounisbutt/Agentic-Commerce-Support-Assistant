"""Core, evidence-first LangGraph support workflow with human interrupt/resume."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any, Protocol, TypedDict
from uuid import uuid4

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field, model_validator

from app.ai.prompts.support import INTENT_CLASSIFICATION_PROMPT, RESPONSE_GENERATION_PROMPT
from app.ai.retrieval.service import KnowledgeRetriever, OpenAIKnowledgeEmbeddings, RetrievalResult
from app.ai.tools.commerce import CommerceTools
from app.core.config import Settings, get_settings
from app.services.commerce_lookup import CommerceLookupService
from sqlalchemy.orm import Session

KNOWLEDGE_MAX_COSINE_DISTANCE = 0.70


def _append(left: list[Any], right: list[Any]) -> list[Any]:
    return left + right


class Intent(str, Enum):
    KNOWLEDGE = "KNOWLEDGE"
    ORDER_LOOKUP = "ORDER_LOOKUP"
    PRODUCT_LOOKUP = "PRODUCT_LOOKUP"
    REFUND_OR_EXCEPTION = "REFUND_OR_EXCEPTION"
    GENERAL_SUPPORT = "GENERAL_SUPPORT"
    UNKNOWN = "UNKNOWN"


class WorkflowStatus(str, Enum):
    COMPLETED = "COMPLETED"
    INTERRUPTED = "INTERRUPTED"


class HumanReviewAction(str, Enum):
    APPROVE = "APPROVE"
    EDIT = "EDIT"
    REJECT = "REJECT"


class HumanReviewDecision(BaseModel):
    action: HumanReviewAction
    edited_response: str | None = None
    reviewer_note: str | None = None

    @model_validator(mode="after")
    def edit_requires_response(self) -> "HumanReviewDecision":
        if self.action is HumanReviewAction.EDIT and not (self.edited_response or "").strip():
            raise ValueError("edited_response is required when action is EDIT.")
        return self


class WorkflowNotFoundError(ValueError):
    """Raised when a requested workflow thread has no persisted state."""


class IntentClassification(BaseModel):
    intent: Intent
    entities: dict[str, str] = Field(default_factory=dict)


class SupportState(TypedDict, total=False):
    conversation_id: str
    run_id: str
    user_message: str
    intent: str
    entities: dict[str, str]
    retrieved_documents: Annotated[list[dict[str, Any]], _append]
    tool_calls: Annotated[list[dict[str, Any]], _append]
    tool_results: Annotated[list[dict[str, Any]], _append]
    draft_response: str
    risk_flags: Annotated[list[str], _append]
    evidence_status: str
    escalation_required: bool
    escalation_reason: str | None
    final_response: str
    graph_path: Annotated[list[str], _append]
    human_review_payload: dict[str, Any]
    human_decision: dict[str, Any]
    workflow_status: str


class EvidenceSource(BaseModel):
    source_name: str
    title: str
    chunk_index: int
    distance: float


class HumanReviewPayload(BaseModel):
    run_id: str
    conversation_id: str
    intent: Intent
    customer_message: str
    proposed_response: str
    escalation_reason: str
    risk_flags: list[str]
    sources: list[EvidenceSource]
    tool_results: list[dict[str, Any]]
    allowed_actions: list[HumanReviewAction]


class WorkflowResult(BaseModel):
    run_id: str
    conversation_id: str | None = None
    intent: Intent
    response: str
    draft_response: str
    evidence_status: str
    sources: list[EvidenceSource]
    tool_results: list[dict[str, Any]]
    escalation_required: bool
    escalation_reason: str | None = None
    risk_flags: list[str]
    graph_path: list[str]
    workflow_status: WorkflowStatus = WorkflowStatus.COMPLETED
    human_review_payload: HumanReviewPayload | None = None


class IntentClassifier(Protocol):
    def classify(self, message: str) -> IntentClassification: ...


class ResponseGenerator(Protocol):
    def generate(self, message: str, intent: Intent, evidence: list[dict[str, Any]]) -> str: ...


class OpenAIIntentClassifier:
    def __init__(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required to run the support workflow.")
        model = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_chat_model)
        self._model = model.with_structured_output(
            IntentClassification,
            method="function_calling",
        )

    def classify(self, message: str) -> IntentClassification:
        return self._model.invoke(f"{INTENT_CLASSIFICATION_PROMPT}\n\nCustomer message: {message}")


class OpenAIResponseGenerator:
    def __init__(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required to run the support workflow.")
        self._model = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_chat_model)

    def generate(self, message: str, intent: Intent, evidence: list[dict[str, Any]]) -> str:
        response = self._model.invoke(
            f"{RESPONSE_GENERATION_PROMPT}\n\nIntent: {intent.value}\n"
            f"Customer message: {message}\nEvidence: {evidence}"
        )
        return str(response.content).strip()


@dataclass(frozen=True)
class WorkflowDependencies:
    classifier: IntentClassifier
    response_generator: ResponseGenerator
    retriever: KnowledgeRetriever
    commerce_tools: CommerceTools


class SupportWorkflow:
    """Compile and invoke a deterministic routing graph around injected application services."""

    def __init__(self, dependencies: WorkflowDependencies, *, checkpointer: InMemorySaver | None = None) -> None:
        self._dependencies = dependencies
        self._checkpointer = checkpointer or InMemorySaver()
        self._graph = self._build_graph()

    def run(self, user_message: str, *, conversation_id: str | None = None) -> WorkflowResult:
        """Backward-compatible alias for starting a workflow thread."""
        return self.start(user_message, conversation_id=conversation_id)

    def start(self, user_message: str, *, conversation_id: str | None = None) -> WorkflowResult:
        thread_id = conversation_id or str(uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        state = self._graph.invoke(
            {
                "user_message": user_message,
                "conversation_id": thread_id,
                "run_id": str(uuid4()),
                "retrieved_documents": [],
                "tool_calls": [],
                "tool_results": [],
                "risk_flags": [],
                "graph_path": [],
            },
            config=config,
        )
        return self._result_from_state(state)

    def resume(self, thread_id: str, decision: HumanReviewDecision) -> WorkflowResult:
        """Resume an interrupted thread through LangGraph's supported Command API."""
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = self._graph.get_state(config)
        if not snapshot.values:
            raise WorkflowNotFoundError(f"Workflow thread {thread_id!r} was not found.")
        if not snapshot.next:
            raise WorkflowNotFoundError(f"Workflow thread {thread_id!r} is not awaiting human review.")
        state = self._graph.invoke(Command(resume=decision.model_dump(mode="json")), config=config)
        return self._result_from_state(state)

    def _result_from_state(self, state: dict[str, Any]) -> WorkflowResult:
        interrupts = state.get("__interrupt__", ())
        payload = None
        if interrupts:
            payload = HumanReviewPayload.model_validate(interrupts[0].value)
        return WorkflowResult(
            run_id=state["run_id"],
            conversation_id=state.get("conversation_id") or None,
            intent=Intent(state["intent"]),
            response=state.get("final_response") or state["draft_response"],
            draft_response=state["draft_response"],
            evidence_status=state["evidence_status"],
            sources=[
                EvidenceSource(
                    source_name=item["source_name"],
                    title=item["title"],
                    chunk_index=item["chunk_index"],
                    distance=item["distance"],
                )
                for item in state.get("retrieved_documents", [])
            ],
            tool_results=state.get("tool_results", []),
            escalation_required=state.get("escalation_required", False),
            escalation_reason=state.get("escalation_reason"),
            risk_flags=state.get("risk_flags", []),
            graph_path=state.get("graph_path", []),
            workflow_status=WorkflowStatus.INTERRUPTED if payload else WorkflowStatus.COMPLETED,
            human_review_payload=payload,
        )

    def _build_graph(self):
        graph = StateGraph(SupportState)
        graph.add_node("prepare_context", self._prepare_context)
        graph.add_node("classify_intent", self._classify_intent)
        graph.add_node("retrieve_knowledge", self._retrieve_knowledge)
        graph.add_node("lookup_order", self._lookup_order)
        graph.add_node("lookup_product", self._lookup_product)
        graph.add_node("prepare_escalation", self._prepare_escalation)
        graph.add_node("human_review", self._human_review)
        graph.add_node("apply_human_decision", self._apply_human_decision)
        graph.add_node("generate_response", self._generate_response)
        graph.add_node("evaluate_response", self._evaluate_response)
        graph.add_node("fallback", self._fallback)
        graph.add_node("finalize", self._finalize)
        graph.add_edge(START, "prepare_context")
        graph.add_edge("prepare_context", "classify_intent")
        graph.add_conditional_edges(
            "classify_intent",
            self._route_intent,
            {
                "knowledge": "retrieve_knowledge",
                "order": "lookup_order",
                "product": "lookup_product",
                "sensitive": "prepare_escalation",
                "fallback": "fallback",
            },
        )
        for node in ("retrieve_knowledge", "lookup_order", "lookup_product"):
            graph.add_edge(node, "generate_response")
        graph.add_edge("prepare_escalation", "human_review")
        graph.add_edge("human_review", "apply_human_decision")
        graph.add_edge("apply_human_decision", "finalize")
        graph.add_edge("generate_response", "evaluate_response")
        graph.add_edge("fallback", "finalize")
        graph.add_edge("evaluate_response", "finalize")
        graph.add_edge("finalize", END)
        return graph.compile(checkpointer=self._checkpointer)

    @staticmethod
    def _prepare_context(state: SupportState) -> dict[str, Any]:
        return {"graph_path": ["prepare_context"]}

    def _classify_intent(self, state: SupportState) -> dict[str, Any]:
        classification = self._dependencies.classifier.classify(state["user_message"])
        return {
            "intent": classification.intent.value,
            "entities": classification.entities,
            "graph_path": ["classify_intent"],
        }

    @staticmethod
    def _route_intent(state: SupportState) -> str:
        return {
            Intent.KNOWLEDGE.value: "knowledge",
            Intent.ORDER_LOOKUP.value: "order",
            Intent.PRODUCT_LOOKUP.value: "product",
            Intent.REFUND_OR_EXCEPTION.value: "sensitive",
        }.get(state["intent"], "fallback")

    def _retrieve_knowledge(self, state: SupportState) -> dict[str, Any]:
        results: list[RetrievalResult] = self._dependencies.retriever.retrieve(state["user_message"])
        evidence = [
            {
                "content": result.content,
                "source_name": result.source_name,
                "title": result.title,
                "chunk_index": result.chunk_index,
                "distance": result.distance,
            }
            for result in results
        ]
        best_distance = min((result.distance for result in results), default=None)
        return {
            "retrieved_documents": evidence,
            "evidence_status": (
                "GROUNDED"
                if best_distance is not None and best_distance <= KNOWLEDGE_MAX_COSINE_DISTANCE
                else "INSUFFICIENT_EVIDENCE"
            ),
            "graph_path": ["retrieve_knowledge"],
        }

    def _lookup_order(self, state: SupportState) -> dict[str, Any]:
        number = state.get("entities", {}).get("order_number", "")
        result = self._dependencies.commerce_tools.lookup_order(number).model_dump(mode="json")
        return {
            "tool_calls": [{"tool": "lookup_order", "arguments": {"order_number": number}}],
            "tool_results": [result],
            "evidence_status": "GROUNDED" if result["found"] else "NOT_FOUND",
            "graph_path": ["lookup_order"],
        }

    def _lookup_product(self, state: SupportState) -> dict[str, Any]:
        entities = state.get("entities", {})
        identifier = entities.get("product_name", "")
        result = self._dependencies.commerce_tools.get_product(
            identifier, size=entities.get("size"), color=entities.get("color")
        ).model_dump(mode="json")
        return {
            "tool_calls": [{"tool": "get_product", "arguments": entities}],
            "tool_results": [result],
            "evidence_status": "GROUNDED" if result["found"] else "NOT_FOUND",
            "graph_path": ["lookup_product"],
        }

    @staticmethod
    def _prepare_escalation(state: SupportState) -> dict[str, Any]:
        return {
            "escalation_required": True,
            "escalation_reason": "Refund, damaged-item, or policy-exception request requires human review.",
            "evidence_status": "REQUIRES_HUMAN_REVIEW",
            "draft_response": "Your request needs review by a support specialist before we can confirm a resolution.",
            "risk_flags": ["SENSITIVE_REQUEST"],
            "workflow_status": "REQUIRES_HUMAN_REVIEW",
            "graph_path": ["prepare_escalation"],
        }

    def _human_review(self, state: SupportState) -> dict[str, Any]:
        payload = HumanReviewPayload(
            run_id=state["run_id"],
            conversation_id=state["conversation_id"],
            intent=Intent(state["intent"]),
            customer_message=state["user_message"],
            proposed_response=state["draft_response"],
            escalation_reason=state["escalation_reason"] or "Human review is required.",
            risk_flags=state.get("risk_flags", []),
            sources=[
                EvidenceSource(
                    source_name=item["source_name"],
                    title=item["title"],
                    chunk_index=item["chunk_index"],
                    distance=item["distance"],
                )
                for item in state.get("retrieved_documents", [])
            ],
            tool_results=state.get("tool_results", []),
            allowed_actions=[
                HumanReviewAction.APPROVE,
                HumanReviewAction.EDIT,
                HumanReviewAction.REJECT,
            ],
        )
        decision = HumanReviewDecision.model_validate(interrupt(payload.model_dump(mode="json")))
        return {
            "human_review_payload": payload.model_dump(mode="json"),
            "human_decision": decision.model_dump(mode="json"),
            "graph_path": ["human_review"],
        }

    @staticmethod
    def _apply_human_decision(state: SupportState) -> dict[str, Any]:
        decision = HumanReviewDecision.model_validate(state["human_decision"])
        if decision.action is HumanReviewAction.APPROVE:
            response = state["draft_response"]
        elif decision.action is HumanReviewAction.EDIT:
            response = decision.edited_response or state["draft_response"]
        else:
            response = "Your request needs additional review before a resolution can be confirmed."
        return {
            "final_response": response,
            "workflow_status": "COMPLETED",
            "graph_path": ["apply_human_decision"],
        }

    def _generate_response(self, state: SupportState) -> dict[str, Any]:
        if state.get("evidence_status") in {"INSUFFICIENT_EVIDENCE", "NOT_FOUND"}:
            return {
                "draft_response": "I couldn't verify that from the available store information.",
                "graph_path": ["generate_response"],
            }
        evidence = [*state.get("retrieved_documents", []), *state.get("tool_results", [])]
        draft = self._dependencies.response_generator.generate(
            state["user_message"], Intent(state["intent"]), evidence
        )
        return {"draft_response": draft, "graph_path": ["generate_response"]}

    @staticmethod
    def _evaluate_response(state: SupportState) -> dict[str, Any]:
        if state.get("escalation_required"):
            return {"final_response": state["draft_response"], "graph_path": ["evaluate_response"]}
        if state.get("evidence_status") in {"INSUFFICIENT_EVIDENCE", "NOT_FOUND"}:
            return {
                "final_response": "I couldn't verify that from the available store information.",
                "risk_flags": ["INSUFFICIENT_EVIDENCE"],
                "graph_path": ["evaluate_response"],
            }
        return {"final_response": state["draft_response"], "graph_path": ["evaluate_response"]}

    @staticmethod
    def _fallback(state: SupportState) -> dict[str, Any]:
        return {
            "evidence_status": "UNSUPPORTED",
            "draft_response": "I couldn't verify that from the available store information.",
            "final_response": "I couldn't verify that from the available store information.",
            "risk_flags": ["UNSUPPORTED_REQUEST"],
            "graph_path": ["fallback"],
        }

    @staticmethod
    def _finalize(state: SupportState) -> dict[str, Any]:
        return {"graph_path": ["finalize"]}


def create_openai_workflow(session: Session, settings: Settings | None = None) -> SupportWorkflow:
    """Wire configured OpenAI clients and existing application services into the graph."""
    settings = settings or get_settings()
    return SupportWorkflow(
        WorkflowDependencies(
            classifier=OpenAIIntentClassifier(settings),
            response_generator=OpenAIResponseGenerator(settings),
            retriever=KnowledgeRetriever(session, OpenAIKnowledgeEmbeddings(settings)),
            commerce_tools=CommerceTools(CommerceLookupService(session)),
        )
    )
