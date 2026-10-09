"""Manual, repeatable ingestion of the small local support-knowledge corpus."""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid5

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.ai.retrieval.service import OpenAIKnowledgeEmbeddings
from app.db.session import SessionLocal
from app.models import KnowledgeChunk, KnowledgeDocument
from app.models.knowledge import KNOWLEDGE_EMBEDDING_DIMENSIONS

_NAMESPACE = UUID("cc7fe875-a299-4454-bec6-99de22a5f8aa")
_SPLITTER = RecursiveCharacterTextSplitter(chunk_size=750, chunk_overlap=100)


class DocumentEmbedder(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


@dataclass(frozen=True)
class LoadedKnowledgeDocument:
    source_name: str
    title: str
    content: str


@dataclass(frozen=True)
class ChunkPayload:
    index: int
    content: str


def document_checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_markdown_documents(directory: Path) -> list[LoadedKnowledgeDocument]:
    """Load source documents in filename order for reproducible ingestion."""
    documents = []
    for path in sorted(directory.glob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError(f"Knowledge document is empty: {path}")
        heading = next((line[2:].strip() for line in content.splitlines() if line.startswith("# ")), None)
        documents.append(
            LoadedKnowledgeDocument(
                source_name=path.name,
                title=heading or path.stem.replace("-", " ").title(),
                content=content,
            )
        )
    if not documents:
        raise ValueError(f"No Markdown knowledge documents found in {directory}")
    return documents


def chunk_document(document: LoadedKnowledgeDocument) -> list[ChunkPayload]:
    """Split Markdown into 750-character chunks with 100-character overlap."""
    return [
        ChunkPayload(index=index, content=content)
        for index, content in enumerate(_SPLITTER.split_text(document.content))
    ]


def ingest_documents(
    session: Session,
    documents: list[LoadedKnowledgeDocument],
    embeddings: DocumentEmbedder,
    *,
    reset: bool = False,
) -> tuple[int, int]:
    """Persist changed documents only and return ``(documents_written, chunks_written)``."""
    if reset:
        session.execute(delete(KnowledgeChunk))
        session.execute(delete(KnowledgeDocument))

    documents_written = 0
    chunks_written = 0
    for source in documents:
        checksum = document_checksum(source.content)
        existing = session.scalar(
            select(KnowledgeDocument).where(KnowledgeDocument.source_name == source.source_name)
        )
        if existing and existing.content_hash == checksum:
            continue
        if existing:
            session.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == existing.id))
            document = existing
            document.title = source.title
            document.content_hash = checksum
        else:
            document = KnowledgeDocument(
                id=uuid5(_NAMESPACE, f"document:{source.source_name}"),
                source_name=source.source_name,
                title=source.title,
                content_hash=checksum,
            )
            session.add(document)

        chunks = chunk_document(source)
        vectors = embeddings.embed_documents([chunk.content for chunk in chunks])
        if len(vectors) != len(chunks):
            raise ValueError("Embedding provider returned a different number of vectors than chunks.")
        for chunk, vector in zip(chunks, vectors, strict=True):
            if len(vector) != KNOWLEDGE_EMBEDDING_DIMENSIONS:
                raise ValueError(
                    "Embedding provider returned a vector that does not match the 1536-dimensional schema."
                )
            session.add(
                KnowledgeChunk(
                    id=uuid5(_NAMESPACE, f"chunk:{source.source_name}:{checksum}:{chunk.index}"),
                    document=document,
                    chunk_index=chunk.index,
                    content=chunk.content,
                    embedding=vector,
                    chunk_metadata={"source_name": source.source_name, "content_hash": checksum},
                )
            )
            chunks_written += 1
        documents_written += 1
    session.flush()
    return documents_written, chunks_written


def _default_knowledge_directory() -> Path:
    return Path(__file__).resolve().parents[5] / "data" / "knowledge"


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest local Markdown support documents into pgvector.")
    parser.add_argument("--reset", action="store_true", help="replace all existing knowledge documents and chunks")
    parser.add_argument("--directory", type=Path, default=_default_knowledge_directory())
    args = parser.parse_args()
    try:
        documents = load_markdown_documents(args.directory)
        embeddings = OpenAIKnowledgeEmbeddings()
        with SessionLocal() as session:
            counts = ingest_documents(session, documents, embeddings, reset=args.reset)
            session.commit()
    except SQLAlchemyError as error:
        raise SystemExit("Knowledge schema is unavailable; run 'alembic upgrade head' first.") from error
    print(f"Ingested {counts[0]} documents and {counts[1]} chunks.")


if __name__ == "__main__":
    main()
