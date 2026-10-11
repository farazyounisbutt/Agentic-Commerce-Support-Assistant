from fastapi.testclient import TestClient

from app.ai.graph.workflow import (
    HumanReviewAction,
    HumanReviewDecision,
    Intent,
    WorkflowResult,
    WorkflowStatus,
)
from app.main import app


class _Workflow:
    def start(self, message: str, *, conversation_id: str | None = None) -> WorkflowResult:
        return WorkflowResult(
            run_id="run-1", conversation_id=conversation_id or "thread-1", intent=Intent.KNOWLEDGE,
            response="Shipping evidence.", draft_response="Shipping evidence.", evidence_status="GROUNDED",
            sources=[], tool_results=[], escalation_required=False, risk_flags=[], graph_path=["finalize"],
        )

    def resume(self, thread_id: str, decision: HumanReviewDecision) -> WorkflowResult:
        return WorkflowResult(
            run_id="run-1", conversation_id=thread_id, intent=Intent.REFUND_OR_EXCEPTION,
            response=decision.edited_response or "Reviewed.", draft_response="Reviewed.",
            evidence_status="REQUIRES_HUMAN_REVIEW", sources=[], tool_results=[],
            escalation_required=True, risk_flags=["SENSITIVE_REQUEST"], graph_path=["finalize"],
            workflow_status=WorkflowStatus.COMPLETED,
        )


def test_chat_and_resume_endpoints_use_application_workflow() -> None:
    app.state.workflow = _Workflow()
    client = TestClient(app)

    chat = client.post("/api/chat", json={"message": "How long does shipping take?", "conversation_id": "browser-1"})
    resume = client.post("/api/chat/browser-1/resume", json={"action": HumanReviewAction.EDIT, "edited_response": "Reviewer update."})

    assert chat.status_code == 200
    assert chat.json()["conversation_id"] == "browser-1"
    assert resume.status_code == 200
    assert resume.json()["response"] == "Reviewer update."


def test_resume_rejects_invalid_edit() -> None:
    app.state.workflow = _Workflow()
    response = TestClient(app).post("/api/chat/thread-1/resume", json={"action": "EDIT"})
    assert response.status_code == 422
