from pydantic import BaseModel, Field

from app.ai.graph.workflow import HumanReviewDecision


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, max_length=255)


class ResumeRequest(HumanReviewDecision):
    pass
