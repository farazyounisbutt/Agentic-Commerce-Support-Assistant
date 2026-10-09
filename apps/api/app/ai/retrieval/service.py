"""Evidence retrieval backed by PostgreSQL and pgvector."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models import KnowledgeChunk, KnowledgeDocument
from app.models.knowledge import KNOWLEDGE_EMBEDDING_DIMENSIONS


class QueryEmbedder(Protocol):
    def embed_query(self, text: str) -> list[float]: ...


class OpenAIKnowledgeEmbeddings:
    """Small adapter that keeps LangChain's embedding client behind a typed interface."""

    def __init__(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for knowledge ingestion and retrieval.")
        if settings.openai_embedding_dimensions != KNOWLEDGE_EMBEDDING_DIMENSIONS:
            raise RuntimeError(
                "OPENAI_EMBEDDING_DIMENSIONS must be 1536 to match the migrated knowledge_chunks schema."
            )
        self._client = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
            dimensions=settings.openai_embedding_dimensions,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._client.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._client.embed_query(text)


@dataclass(frozen=True)
class RetrievalResult:
    content: str
    source_name: str
    title: str
    chunk_index: int
    metadata: dict[str, Any]
    distance: float


class KnowledgeRetriever:
    """Return grounded chunks only; response generation belongs to a later workflow layer."""

    def __init__(self, session: Session, embeddings: QueryEmbedder) -> None:
        self._session = session
        self._embeddings = embeddings

    def retrieve(self, query: str, *, top_k: int = 4) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError("A retrieval query must not be empty.")
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        embedding = self._embeddings.embed_query(query)
        distance = KnowledgeChunk.embedding.cosine_distance(embedding).label("distance")
        statement = (
            select(
                KnowledgeChunk.content,
                KnowledgeDocument.source_name,
                KnowledgeDocument.title,
                KnowledgeChunk.chunk_index,
                KnowledgeChunk.chunk_metadata,
                distance,
            )
            .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
            .order_by(distance)
            .limit(top_k)
        )
        return [
            RetrievalResult(
                content=row[0],
                source_name=row[1],
                title=row[2],
                chunk_index=row[3],
                metadata=row[4],
                distance=float(row[5]),
            )
            for row in self._session.execute(statement).all()
        ]
