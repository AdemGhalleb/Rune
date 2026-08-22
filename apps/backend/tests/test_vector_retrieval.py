from dataclasses import dataclass

import pytest
from sqlalchemy import select

from app.core.config import Settings
from app.db.models import (
    Chunk,
    Conversation,
    DocumentProcessing,
    DocumentSegment,
    Message,
    MessageSource,
    Workspace,
    WorkspaceFile,
)
from app.db.vector_store import SQLiteChunkVectorStore
from app.services.rag import RagService
from app.services.retrieval import RetrievedChunk, RetrievalService


@dataclass
class FakeEmbeddingProvider:
    vectors: dict[str, list[float]]

    async def embed(self, text: str) -> list[float]:
        if text not in self.vectors:
            raise KeyError(f"Missing test embedding for {text!r}")
        return self.vectors[text]

    async def is_available(self) -> bool:
        return True


class FakeProvider:
    async def is_available(self) -> bool:
        return True

    async def generate(self, prompt: str) -> str:
        return "answer"

    async def stream(self, prompt: str):
        yield "answer"


@pytest.fixture
def vector_store(session_factory):
    store = SQLiteChunkVectorStore(
        session_factory,
        embedding_provider=FakeEmbeddingProvider(
            {
                "what is calculus": [1.0, 0.0, 0.0],
                "what is biology": [0.0, 1.0, 0.0],
                "what is astronomy": [0.0, 0.0, 1.0],
            }
        ),
        dimension=3,
    )
    yield store


@pytest.mark.asyncio
async def test_vector_search_round_trip_and_workspace_isolation(session_factory, vector_store):
    with session_factory() as session:
        workspace_a = Workspace(root_path="/ws/a", name="Course A")
        workspace_b = Workspace(root_path="/ws/b", name="Course B")
        session.add_all([workspace_a, workspace_b])
        session.commit()
        session.refresh(workspace_a)
        session.refresh(workspace_b)

        file_a = WorkspaceFile(
            workspace_id=workspace_a.id,
            relative_path="notes.md",
            filename="notes.md",
            extension="md",
            category="note",
            size_bytes=128,
            modified_at=session.bind.connect()
            .cursor()
            .execute("SELECT CURRENT_TIMESTAMP")
            .fetchone()[0]
            if False
            else __import__("datetime").datetime.utcnow(),
            content_hash="hash-a",
            fs_status="unchanged",
        )
        file_b = WorkspaceFile(
            workspace_id=workspace_b.id,
            relative_path="other.md",
            filename="other.md",
            extension="md",
            category="note",
            size_bytes=128,
            modified_at=__import__("datetime").datetime.utcnow(),
            content_hash="hash-b",
            fs_status="unchanged",
        )
        session.add_all([file_a, file_b])
        session.commit()
        session.refresh(file_a)
        session.refresh(file_b)

        doc_a = DocumentProcessing(
            workspace_file_id=file_a.id, extraction_status="extracted", chunking_status="chunked"
        )
        doc_b = DocumentProcessing(
            workspace_file_id=file_b.id, extraction_status="extracted", chunking_status="chunked"
        )
        session.add_all([doc_a, doc_b])
        session.commit()
        session.refresh(doc_a)
        session.refresh(doc_b)

        seg_a = DocumentSegment(
            document_processing_id=doc_a.id,
            segment_index=0,
            segment_type="plain_text",
            text="Calculus means limits and integrals.",
            char_count=40,
        )
        seg_b = DocumentSegment(
            document_processing_id=doc_b.id,
            segment_index=0,
            segment_type="plain_text",
            text="Biology studies cells and ecosystems.",
            char_count=38,
        )
        session.add_all([seg_a, seg_b])
        session.commit()
        session.refresh(seg_a)
        session.refresh(seg_b)

        chunk_a = Chunk(
            document_processing_id=doc_a.id,
            segment_id=seg_a.id,
            chunk_index=0,
            text="Calculus covers limits, derivatives, and integrals.",
            char_start=0,
            char_end=60,
            char_count=60,
            content_hash="chunk-a",
        )
        chunk_b = Chunk(
            document_processing_id=doc_b.id,
            segment_id=seg_b.id,
            chunk_index=0,
            text="Biology is not calculus; it studies cells.",
            char_start=0,
            char_end=50,
            char_count=50,
            content_hash="chunk-b",
        )
        session.add_all([chunk_a, chunk_b])
        session.commit()
        session.refresh(chunk_a)
        session.refresh(chunk_b)

        await vector_store.index_chunk(
            chunk_id=chunk_a.id,
            workspace_id=workspace_a.id,
            vector=[1.0, 0.0, 0.0],
            embedding_model_id="test-model",
        )
        await vector_store.index_chunk(
            chunk_id=chunk_b.id,
            workspace_id=workspace_b.id,
            vector=[0.0, 1.0, 0.0],
            embedding_model_id="test-model",
        )

        hits = await vector_store.search("what is calculus", workspace_id=workspace_a.id, top_k=5)
        assert [hit.chunk_id for hit in hits] == [chunk_a.id]
        assert hits[0].filename == "notes.md"
        assert hits[0].workspace_file_id == file_a.id

        other_workspace = await vector_store.search(
            "what is biology", workspace_id=workspace_a.id, top_k=5
        )
        assert [hit.workspace_file_id for hit in other_workspace] == [file_a.id]
        assert other_workspace[0].score < 0.01


@pytest.mark.asyncio
async def test_rag_uses_retrieval_and_source_metadata(session_factory, tmp_path):
    settings = Settings(
        data_dir=tmp_path, rag_context_token_budget=500, rag_max_chunks_per_document=2
    )
    with session_factory() as session:
        workspace = Workspace(root_path="/ws/c", name="Course C")
        session.add(workspace)
        session.commit()
        session.refresh(workspace)

        workspace_file = WorkspaceFile(
            workspace_id=workspace.id,
            relative_path="study.md",
            filename="study.md",
            extension="md",
            category="note",
            size_bytes=42,
            modified_at=__import__("datetime").datetime.utcnow(),
            content_hash="hash-c",
            fs_status="unchanged",
        )
        session.add(workspace_file)
        session.commit()
        session.refresh(workspace_file)

        doc = DocumentProcessing(
            workspace_file_id=workspace_file.id,
            extraction_status="extracted",
            chunking_status="chunked",
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)

        seg = DocumentSegment(
            document_processing_id=doc.id,
            segment_index=0,
            segment_type="plain_text",
            text="The Moon causes tides.",
            char_count=21,
        )
        session.add(seg)
        session.commit()
        session.refresh(seg)

        chunk = Chunk(
            document_processing_id=doc.id,
            segment_id=seg.id,
            chunk_index=0,
            text="The Moon causes tides on Earth.",
            char_start=0,
            char_end=32,
            char_count=32,
            content_hash="chunk-c",
        )
        session.add(chunk)
        session.commit()
        session.refresh(chunk)

        store = SQLiteChunkVectorStore(
            session_factory,
            embedding_provider=FakeEmbeddingProvider({"what causes tides": [1.0, 0.0, 0.0]}),
            dimension=3,
        )
        await store.index_chunk(
            chunk_id=chunk.id,
            workspace_id=workspace.id,
            vector=[1.0, 0.0, 0.0],
            embedding_model_id="test-model",
        )

        retrieval = RetrievalService(store, workspace_id=workspace.id)
        plan = await RagService(retrieval, FakeProvider(), settings).prepare(
            "what causes tides", []
        )

        assert len(plan.sources) == 1
        assert plan.sources[0].chunk_id == chunk.id
        assert plan.sources[0].workspace_file_id == workspace_file.id
        assert "study.md" in plan.prompt
        assert "The Moon causes tides" in plan.prompt

        conversation = Conversation(title="Tides")
        session.add(conversation)
        session.commit()
        message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content="",
            status="complete",
        )
        session.add(message)
        session.commit()
        session.refresh(message)

        with session_factory() as msg_session:
            msg_session.add(
                MessageSource(
                    message_id=message.id,
                    chunk_id=chunk.id,
                    workspace_file_id=workspace_file.id,
                    rank=1,
                    relevance_score=plan.sources[0].score,
                )
            )
            msg_session.commit()

        assert (
            session.scalar(
                select(MessageSource.chunk_id).where(MessageSource.message_id == message.id)
            )
            == chunk.id
        )


@pytest.mark.asyncio
async def test_empty_retrieval_is_graceful_and_duplicate_chunks_are_filtered(
    session_factory, tmp_path
):
    settings = Settings(
        data_dir=tmp_path, rag_similarity_threshold=0.3, rag_max_chunks_per_document=2
    )
    store = SQLiteChunkVectorStore(
        session_factory,
        embedding_provider=FakeEmbeddingProvider({"query": [1.0, 0.0, 0.0]}),
        dimension=3,
    )

    with session_factory() as session:
        workspace = Workspace(root_path="/ws/d", name="Course D")
        session.add(workspace)
        session.commit()
        session.refresh(workspace)

        file_rec = WorkspaceFile(
            workspace_id=workspace.id,
            relative_path="empty.md",
            filename="empty.md",
            extension="md",
            category="note",
            size_bytes=12,
            modified_at=__import__("datetime").datetime.utcnow(),
            content_hash="hash-d",
            fs_status="unchanged",
        )
        session.add(file_rec)
        session.commit()
        session.refresh(file_rec)

        doc = DocumentProcessing(
            workspace_file_id=file_rec.id, extraction_status="extracted", chunking_status="chunked"
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)

        seg = DocumentSegment(
            document_processing_id=doc.id,
            segment_index=0,
            segment_type="plain_text",
            text="irrelevant text",
            char_count=15,
        )
        session.add(seg)
        session.commit()
        session.refresh(seg)

        chunk = Chunk(
            document_processing_id=doc.id,
            segment_id=seg.id,
            chunk_index=0,
            text="irrelevant text",
            char_start=0,
            char_end=15,
            char_count=15,
            content_hash="chunk-d",
        )
        session.add(chunk)
        session.commit()
        session.refresh(chunk)

        await store.index_chunk(
            chunk_id=chunk.id,
            workspace_id=workspace.id,
            vector=[0.0, 0.1, 0.0],
            embedding_model_id="test-model",
        )

    plan = await RagService(
        RetrievalService(store, workspace_id=workspace.id), FakeProvider(), settings
    ).prepare("query", [])
    assert plan.sources == []
    assert "No relevant reference material was found." in plan.prompt

    duplicate = [
        RetrievedChunk(chunk_id=1, workspace_file_id=10, filename="a.md", text="x", score=0.9),
        RetrievedChunk(chunk_id=1, workspace_file_id=10, filename="a.md", text="x", score=0.8),
    ]

    class FakeVectorStore:
        async def search(self, query: str, *, workspace_id: int, top_k: int) -> list[RetrievedChunk]:
            return duplicate

    deduped = await RagService(
        RetrievalService(FakeVectorStore(), workspace_id=workspace.id),
        FakeProvider(),
        settings,
    ).prepare("query", [])
    assert [source.chunk_id for source in deduped.sources] == [1]
