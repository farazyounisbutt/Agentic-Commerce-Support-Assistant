from dataclasses import dataclass

import pytest

from app.ai.graph.workflow import (
    HumanReviewAction,
    HumanReviewDecision,
    Intent,
    IntentClassification,
    SupportWorkflow,
    WorkflowNotFoundError,
    WorkflowStatus,
    WorkflowDependencies,
)
from app.ai.retrieval.service import RetrievalResult


@dataclass
class _Result:
    payload: dict

    def model_dump(self, mode: str = "json") -> dict:
        return self.payload


class _Classifier:
    def classify(self, message: str) -> IntentClassification:
        text = message.casefold()
        if "ord-1007" in text:
            return IntentClassification(intent=Intent.ORDER_LOOKUP, entities={"order_number": "ORD-1007"})
        if "trail runner" in text:
            return IntentClassification(
                intent=Intent.PRODUCT_LOOKUP,
                entities={"product_name": "SH-TRAIL-RUNNER", "size": "10"},
            )
        if "refund" in text or "damaged" in text:
            return IntentClassification(intent=Intent.REFUND_OR_EXCEPTION)
        if "shipping" in text:
            return IntentClassification(intent=Intent.KNOWLEDGE)
        return IntentClassification(intent=Intent.UNKNOWN)


class _Retriever:
    def __init__(self, results: list[RetrievalResult]) -> None:
        self.results = results

    def retrieve(self, query: str, *, top_k: int = 4) -> list[RetrievalResult]:
        return self.results


class _CommerceTools:
    def lookup_order(self, order_number: str) -> _Result:
        return _Result({"found": order_number == "ORD-1007", "order": {"order_number": order_number}})

    def get_product(self, identifier: str, *, size: str | None = None, color: str | None = None) -> _Result:
        found = identifier == "SH-TRAIL-RUNNER"
        return _Result(
            {
                "found": found,
                "product": {"name": "Trail Runner Shoes"} if found else None,
                "matching_variants": [{"sku": "SH-TRAIL-RUNNER-PINE-10", "available": True}]
                if found
                else [],
            }
        )


class _Generator:
    def generate(self, message: str, intent: Intent, evidence: list[dict]) -> str:
        return f"Grounded {intent.value} response."


class _FixedClassifier:
    def __init__(self, classification: IntentClassification) -> None:
        self._classification = classification

    def classify(self, message: str) -> IntentClassification:
        return self._classification


def _workflow(*, evidence: list[RetrievalResult] | None = None) -> SupportWorkflow:
    return SupportWorkflow(
        WorkflowDependencies(
            classifier=_Classifier(),
            response_generator=_Generator(),
            retriever=_Retriever(evidence or []),
            commerce_tools=_CommerceTools(),
        )
    )


def test_shipping_question_routes_to_knowledge_with_evidence() -> None:
    result = _workflow(
        evidence=[
            RetrievalResult("Standard shipping takes three to five days.", "shipping-policy.md", "Shipping Policy", 0, {}, 0.1)
        ]
    ).run("How long does standard shipping take?")

    assert result.intent is Intent.KNOWLEDGE
    assert result.workflow_status is WorkflowStatus.COMPLETED
    assert result.evidence_status == "GROUNDED"
    assert "retrieve_knowledge" in result.graph_path
    assert result.sources[0].source_name == "shipping-policy.md"


def test_weak_knowledge_match_is_insufficient_evidence() -> None:
    result = _workflow(
        evidence=[
            RetrievalResult(
                "Unrelated policy text.",
                "shipping-policy.md",
                "Shipping Policy",
                0,
                {},
                0.75,
            )
        ]
    ).run("How long does standard shipping take?")

    assert result.evidence_status == "INSUFFICIENT_EVIDENCE"
    assert result.sources[0].distance == 0.75
    assert "couldn't verify" in result.response.casefold()
    assert "INSUFFICIENT_EVIDENCE" in result.risk_flags


def test_order_and_product_messages_route_to_typed_tools() -> None:
    order = _workflow().run("Where is ORD-1007?")
    product = _workflow().run("Do you have Trail Runner shoes in size 10?")

    assert order.intent is Intent.ORDER_LOOKUP
    assert order.workflow_status is WorkflowStatus.COMPLETED
    assert order.evidence_status == "GROUNDED"
    assert order.tool_results[0]["found"] is True
    assert product.intent is Intent.PRODUCT_LOOKUP
    assert product.workflow_status is WorkflowStatus.COMPLETED
    assert product.tool_results[0]["matching_variants"][0]["available"] is True


def test_sensitive_request_interrupts_with_structured_review_payload() -> None:
    result = _workflow().start("My order arrived damaged. Refund it.", conversation_id="review-thread")

    assert result.intent is Intent.REFUND_OR_EXCEPTION
    assert result.workflow_status is WorkflowStatus.INTERRUPTED
    assert result.escalation_required is True
    assert result.evidence_status == "REQUIRES_HUMAN_REVIEW"
    assert result.human_review_payload is not None
    assert result.human_review_payload.conversation_id == "review-thread"
    assert result.human_review_payload.allowed_actions == [
        HumanReviewAction.APPROVE,
        HumanReviewAction.EDIT,
        HumanReviewAction.REJECT,
    ]


def test_human_decisions_resume_the_same_interrupted_thread() -> None:
    workflow = _workflow()

    approved = workflow.start("My order arrived damaged. Refund it.", conversation_id="approve-thread")
    approved_result = workflow.resume(
        "approve-thread", HumanReviewDecision(action=HumanReviewAction.APPROVE)
    )
    assert approved_result.workflow_status is WorkflowStatus.COMPLETED
    assert approved_result.response == approved.draft_response

    workflow.start("My order arrived damaged. Refund it.", conversation_id="edit-thread")
    edited_result = workflow.resume(
        "edit-thread",
        HumanReviewDecision(action=HumanReviewAction.EDIT, edited_response="We will review the photos first."),
    )
    assert edited_result.response == "We will review the photos first."

    workflow.start("My order arrived damaged. Refund it.", conversation_id="reject-thread")
    rejected_result = workflow.resume(
        "reject-thread", HumanReviewDecision(action=HumanReviewAction.REJECT)
    )
    assert rejected_result.response == "Your request needs additional review before a resolution can be confirmed."


def test_invalid_edit_and_unknown_thread_fail_clearly() -> None:
    with pytest.raises(ValueError, match="edited_response"):
        HumanReviewDecision(action=HumanReviewAction.EDIT)

    with pytest.raises(WorkflowNotFoundError, match="unknown-thread"):
        _workflow().resume("unknown-thread", HumanReviewDecision(action=HumanReviewAction.APPROVE))


def test_unknown_and_missing_evidence_use_safe_fallbacks() -> None:
    unknown = _workflow().run("Does every product have a lifetime warranty?")
    missing_evidence = _workflow().run("What is your shipping policy?")

    assert unknown.evidence_status == "UNSUPPORTED"
    assert "fallback" in unknown.graph_path
    assert missing_evidence.evidence_status == "INSUFFICIENT_EVIDENCE"
    assert "couldn't verify" in missing_evidence.response.casefold()


def test_missing_order_and_product_evidence_do_not_hallucinate() -> None:
    def run_with(classification: IntentClassification) -> str:
        workflow = SupportWorkflow(
            WorkflowDependencies(
                classifier=_FixedClassifier(classification),
                response_generator=_Generator(),
                retriever=_Retriever([]),
                commerce_tools=_CommerceTools(),
            )
        )
        return workflow.run("lookup request").response

    missing_order = run_with(
        IntentClassification(intent=Intent.ORDER_LOOKUP, entities={"order_number": "ORD-9999"})
    )
    missing_product = run_with(
        IntentClassification(intent=Intent.PRODUCT_LOOKUP, entities={"product_name": "UNKNOWN"})
    )

    assert "couldn't verify" in missing_order.casefold()
    assert "couldn't verify" in missing_product.casefold()
