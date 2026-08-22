"""Retrieval boundary for RAG; database details stay out of HTTP handlers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: int
    workspace_file_id: int
    filename: str
    text: str
    score: float


class RetrievalService:
    """Workspace-scoped adapter over the Phase 3 vector store."""

    def __init__(self, vector_store: object | None = None, workspace_id: int | None = None) -> None:
        self.vector_store = vector_store
        self.workspace_id = workspace_id

    async def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        if self.vector_store is None or self.workspace_id is None:
            return []
        if hasattr(self.vector_store, "search"):
            return await self.vector_store.search(query, workspace_id=self.workspace_id, top_k=top_k)
        return []
