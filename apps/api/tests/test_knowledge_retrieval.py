from pathlib import Path

from pgvector.sqlalchemy import VECTOR

from app.ai.retrieval.ingest import chunk_document, document_checksum, load_markdown_documents
from app.ai.retrieval.service import KnowledgeRetriever, RetrievalResult
from app.db.base import Base
from app.models import KnowledgeChunk, KnowledgeDocument


def test_knowledge_models_use_a_fixed_pgvector_embedding_and_document_identity() -> None:
    documents = Base.metadata.tables["knowledge_documents"]
    chunks = Base.metadata.tables["knowledge_chunks"]

    assert documents.c.source_name.unique
    assert isinstance(chunks.c.embedding.type, VECTOR)
    assert chunks.c.embedding.type.dim == 1536
    assert {constraint.name for constraint in chunks.constraints} >= {"uq_knowledge_chunks_document_index"}
    assert KnowledgeDocument.chunks.property.back_populates == "document"
    assert KnowledgeChunk.document.property.back_populates == "chunks"


def test_markdown_loading_and_chunking_are_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "shipping-policy.md"
    source.write_text("# Shipping Policy\n\nOrders leave our warehouse within two business days.\n", encoding="utf-8")

    first = load_markdown_documents(tmp_path)
    second = load_markdown_documents(tmp_path)
    first_chunks = chunk_document(first[0])
    second_chunks = chunk_document(second[0])

    assert first[0].source_name == "shipping-policy.md"
    assert first[0].title == "Shipping Policy"
    assert document_checksum(first[0].content) == document_checksum(second[0].content)
    assert [(chunk.index, chunk.content) for chunk in first_chunks] == [
        (chunk.index, chunk.content) for chunk in second_chunks
    ]


def test_retriever_returns_structured_sources_and_honors_top_k() -> None:
    class FakeEmbeddings:
        def embed_query(self, query: str) -> list[float]:
            assert query == "How long does shipping take?"
            return [0.1] * 1536

    class FakeResult:
        def all(self) -> list[tuple[object, ...]]:
            return [
                ("Orders leave within two business days.", "shipping-policy.md", "Shipping Policy", 0, {"checksum": "abc"}, 0.12),
                ("Tracking is emailed after shipment.", "faq.md", "Frequently Asked Questions", 1, {"checksum": "def"}, 0.28),
            ]

    class FakeSession:
        def execute(self, statement: object) -> FakeResult:
            assert "LIMIT" in str(statement)
            return FakeResult()

    results = KnowledgeRetriever(FakeSession(), FakeEmbeddings()).retrieve(
        "How long does shipping take?", top_k=2
    )

    assert results == [
        RetrievalResult(
            content="Orders leave within two business days.",
            source_name="shipping-policy.md",
            title="Shipping Policy",
            chunk_index=0,
            metadata={"checksum": "abc"},
            distance=0.12,
        ),
        RetrievalResult(
            content="Tracking is emailed after shipment.",
            source_name="faq.md",
            title="Frequently Asked Questions",
            chunk_index=1,
            metadata={"checksum": "def"},
            distance=0.28,
        ),
    ]
