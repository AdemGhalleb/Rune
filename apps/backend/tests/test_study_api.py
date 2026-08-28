import json
from datetime import UTC, datetime

from httpx import AsyncClient

from app.ai.providers.base import LLMProvider, LLMProviderUnavailable
from app.db.models import Chunk, DocumentProcessing, DocumentSegment, Workspace, WorkspaceFile
from app.services.retrieval import RetrievedChunk

CHUNK_TEXT = (
    "Operating systems manage hardware resources through scheduling and memory abstraction."
)


class FakeVectorStore:
    def __init__(self, chunks: list[RetrievedChunk] | None = None) -> None:
        self.chunks = chunks or []

    async def search(
        self,
        query: str,
        *,
        workspace_id: int,
        top_k: int,
        workspace_file_id: int | None = None,
    ) -> list[RetrievedChunk]:
        if workspace_file_id is not None:
            return [c for c in self.chunks if c.workspace_file_id == workspace_file_id][:top_k]
        return self.chunks[:top_k]

    def get_chunks_for_file(
        self,
        *,
        workspace_id: int,
        workspace_file_id: int,
        limit: int = 20,
    ) -> list[RetrievedChunk]:
        return [c for c in self.chunks if c.workspace_file_id == workspace_file_id][:limit]


class MockLLM(LLMProvider):
    def __init__(self, response: str = "{}", available: bool = True) -> None:
        self.response = response
        self.available = available

    async def is_available(self) -> bool:
        return self.available

    async def generate(self, prompt: str) -> str:
        if not self.available:
            raise LLMProviderUnavailable("Ollama is not running")
        return self.response

    async def stream(self, prompt: str):
        if not self.available:
            raise LLMProviderUnavailable("Ollama is not running")
        yield self.response


async def test_study_endpoints_without_workspace_return_400(client: AsyncClient):
    resp = await client.post("/api/v1/study/summary", json={"topic": "OS"})
    assert resp.status_code == 400
    assert "No active workspace" in resp.json()["detail"]

    resp = await client.post("/api/v1/study/flashcards", json={"topic": "OS"})
    assert resp.status_code == 400

    resp = await client.post("/api/v1/study/quiz", json={"topic": "OS"})
    assert resp.status_code == 400

    resp = await client.post("/api/v1/study/explain", json={"topic": "OS"})
    assert resp.status_code == 400


async def test_study_endpoints_workflow(client: AsyncClient, app, session_factory, tmp_path):
    ws_dir = tmp_path / "study_workspace"
    ws_dir.mkdir()

    # Seed database with a workspace, file, and chunk
    with session_factory() as session:
        ws = Workspace(name="Test WS", root_path=str(ws_dir))
        session.add(ws)
        session.flush()

        wf = WorkspaceFile(
            workspace_id=ws.id,
            relative_path="lecture1.pdf",
            filename="lecture1.pdf",
            extension=".pdf",
            category="document",
            size_bytes=1000,
            modified_at=datetime.now(UTC),
            fs_status="unchanged",
        )
        session.add(wf)
        session.flush()

        dp = DocumentProcessing(
            workspace_file_id=wf.id,
            extraction_status="extracted",
            chunking_status="chunked",
        )
        session.add(dp)
        session.flush()

        seg = DocumentSegment(
            document_processing_id=dp.id,
            segment_index=0,
            segment_type="pdf_page",
            page_number=1,
            text=CHUNK_TEXT,
            char_count=len(CHUNK_TEXT),
        )
        session.add(seg)
        session.flush()

        chunk = Chunk(
            document_processing_id=dp.id,
            segment_id=seg.id,
            chunk_index=0,
            text=seg.text,
            char_start=0,
            char_end=len(CHUNK_TEXT),
            char_count=len(CHUNK_TEXT),
            content_hash="dummyhash",
        )
        session.add(chunk)
        session.commit()

        file_id = wf.id
        chunk_id = chunk.id

    mock_chunk = RetrievedChunk(
        chunk_id=chunk_id,
        workspace_file_id=file_id,
        filename="lecture1.pdf",
        text=CHUNK_TEXT,
        score=0.9,
    )
    app.state.vector_store = FakeVectorStore([mock_chunk])

    # 1. Summary Endpoint
    summary_json = json.dumps(
        {
            "title": "Operating Systems Core",
            "overview": "Operating systems manage hardware resources.",
            "key_points": ["Resource management", "Memory abstraction"],
            "source_ids": [1],
        }
    )
    app.state.ollama_provider = MockLLM(summary_json)
    resp = await client.post("/api/v1/study/summary", json={"topic": "OS"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Operating Systems Core"
    assert len(data["citations"]) == 1
    assert data["citations"][0]["filename"] == "lecture1.pdf"

    # 2. Flashcards Endpoint
    flashcards_json = json.dumps(
        {
            "cards": [
                {
                    "question": "What is the primary role of an OS?",
                    "answer": "To manage hardware resources and abstract memory.",
                    "source_ids": [1],
                }
            ]
        }
    )
    app.state.ollama_provider = MockLLM(flashcards_json)
    resp = await client.post("/api/v1/study/flashcards", json={"topic": "OS", "count": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["cards"]) == 1
    assert data["cards"][0]["question"] == "What is the primary role of an OS?"
    assert data["cards"][0]["citations"][0]["chunk_id"] == chunk_id

    # 3. Quiz Endpoint
    quiz_json = json.dumps(
        {
            "questions": [
                {
                    "question": "Which of the following is a primary task of an operating system?",
                    "options": [
                        "Managing hardware resources",
                        "Synthesizing music",
                        "Compiling web templates",
                        "Browsing internet archives",
                    ],
                    "correct_index": 0,
                    "explanation": "Operating systems coordinate CPU, memory, and devices.",
                    "source_ids": [1],
                }
            ]
        }
    )
    app.state.ollama_provider = MockLLM(quiz_json)
    resp = await client.post("/api/v1/study/quiz", json={"topic": "OS", "count": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["questions"]) == 1
    assert data["questions"][0]["correct_index"] == 0
    assert len(data["questions"][0]["options"]) == 4

    # 4. Explanation Endpoint
    explain_json = json.dumps(
        {
            "topic": "OS Abstraction",
            "explanation": "Abstraction hides raw hardware complexity behind clean interfaces.",
            "key_takeaways": ["Simplifies programming", "Protects hardware"],
            "source_ids": [1],
        }
    )
    app.state.ollama_provider = MockLLM(explain_json)
    resp = await client.post("/api/v1/study/explain", json={"topic": "OS Abstraction"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["topic"] == "OS Abstraction"
    assert len(data["key_takeaways"]) == 2

    # 5. Offline Provider Error (503)
    app.state.ollama_provider = MockLLM(available=False)
    resp = await client.post("/api/v1/study/summary", json={"topic": "OS"})
    assert resp.status_code == 503
    assert "unavailable" in resp.json()["detail"].lower()

    # 6. Insufficient Context Error (422)
    app.state.vector_store = FakeVectorStore([])
    app.state.ollama_provider = MockLLM(summary_json)
    resp = await client.post("/api/v1/study/summary", json={"topic": "Nonexistent Topic"})
    assert resp.status_code == 422
    assert "No relevant study material" in resp.json()["detail"]
