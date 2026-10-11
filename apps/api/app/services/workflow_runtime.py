"""Process-lifetime workflow runtime with request-operation database sessions."""

from collections.abc import Callable

from sqlalchemy.orm import Session

from app.ai.graph.workflow import (
    OpenAIIntentClassifier,
    OpenAIResponseGenerator,
    SupportWorkflow,
    WorkflowDependencies,
)
from app.ai.retrieval.service import KnowledgeRetriever, OpenAIKnowledgeEmbeddings
from app.ai.tools.commerce import CommerceTools
from app.core.config import Settings, get_settings
from app.services.commerce_lookup import CommerceLookupService


class _ScopedRetriever:
    def __init__(self, session_factory: Callable[[], Session], embeddings: OpenAIKnowledgeEmbeddings) -> None:
        self._session_factory = session_factory
        self._embeddings = embeddings

    def retrieve(self, query: str, *, top_k: int = 4):
        with self._session_factory() as session:
            return KnowledgeRetriever(session, self._embeddings).retrieve(query, top_k=top_k)


class _ScopedCommerceTools:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def lookup_order(self, order_number: str):
        with self._session_factory() as session:
            return CommerceTools(CommerceLookupService(session)).lookup_order(order_number)

    def get_product(self, identifier: str, *, size: str | None = None, color: str | None = None):
        with self._session_factory() as session:
            return CommerceTools(CommerceLookupService(session)).get_product(identifier, size=size, color=color)


def create_workflow_runtime(session_factory: Callable[[], Session], settings: Settings | None = None) -> SupportWorkflow:
    """Create one graph/checkpointer while keeping each database operation request-scoped."""
    settings = settings or get_settings()
    embeddings = OpenAIKnowledgeEmbeddings(settings)
    return SupportWorkflow(
        WorkflowDependencies(
            classifier=OpenAIIntentClassifier(settings),
            response_generator=OpenAIResponseGenerator(settings),
            retriever=_ScopedRetriever(session_factory, embeddings),  # type: ignore[arg-type]
            commerce_tools=_ScopedCommerceTools(session_factory),  # type: ignore[arg-type]
        )
    )
