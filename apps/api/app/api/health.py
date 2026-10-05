from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return basic API availability without requiring external services."""
    return HealthResponse(status="ok", service="agentic-commerce-support-api")

