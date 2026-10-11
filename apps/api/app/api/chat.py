from fastapi import APIRouter, HTTPException, Request

from app.ai.graph.workflow import WorkflowNotFoundError, WorkflowResult
from app.db.session import SessionLocal
from app.schemas.chat import ChatRequest, ResumeRequest
from app.services.workflow_runtime import create_workflow_runtime

router = APIRouter(tags=["chat"])


def _workflow(request: Request):
    workflow = getattr(request.app.state, "workflow", None)
    if workflow is None:
        workflow = create_workflow_runtime(SessionLocal)
        request.app.state.workflow = workflow
    return workflow


@router.post("/chat", response_model=WorkflowResult)
def start_chat(payload: ChatRequest, request: Request) -> WorkflowResult:
    try:
        return _workflow(request).start(payload.message, conversation_id=payload.conversation_id)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail="Support workflow is currently unavailable.") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Support workflow failed.") from error


@router.post("/chat/{conversation_id}/resume", response_model=WorkflowResult)
def resume_chat(conversation_id: str, payload: ResumeRequest, request: Request) -> WorkflowResult:
    try:
        return _workflow(request).resume(conversation_id, payload)
    except WorkflowNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail="Support workflow is currently unavailable.") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Support workflow failed.") from error
