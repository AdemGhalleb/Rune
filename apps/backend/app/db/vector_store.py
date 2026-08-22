"""Minimal sqlite-vec-backed chunk vector store for Phase 3 retrieval."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.ai.embeddings.config import ACTIVE_EMBEDDING_DIMENSION, get_active_embedding_model_id
from app.ai.providers.base import EmbeddingProvider
from app.db.models import Chunk, WorkspaceFile
from app.services.retrieval import RetrievedChunk


@dataclass(frozen=True)
class VectorSearchHit:
    chunk_id: int
    workspace_file_id: int
    filename: str
    text: str
    score: float


class SQLiteChunkVectorStore:
    """Store and query chunk embeddings in SQLite using sqlite-vec."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        embedding_provider: EmbeddingProvider | None = None,
        *,
        table_name: str = "chunk_vectors",
        dimension: int = ACTIVE_EMBEDDING_DIMENSION,
    ) -> None:
        self.session_factory = session_factory
        self.embedding_provider = embedding_provider
        self.table_name = table_name
        self.dimension = dimension

    async def embed_query(self, query: str) -> list[float]:
        if self.embedding_provider is None:
            raise ValueError("Embedding provider is required for query embedding")
        return await self.embedding_provider.embed(query)

    async def index_chunk(
        self,
        *,
        chunk_id: int,
        workspace_id: int,
        vector: list[float],
        embedding_model_id: str | None = None,
    ) -> None:
        if len(vector) != self.dimension:
            raise ValueError(f"Expected {self.dimension}-dimensional vector, got {len(vector)}")
        model_id = embedding_model_id or get_active_embedding_model_id()
        with self.session_factory() as session:
            self._ensure_vector_table(session, model_id)
            session.execute(
                text(
                    f"INSERT INTO {self.table_name}(chunk_id, workspace_id, embedding_model_id, vector) "
                    "VALUES (:chunk_id, :workspace_id, :embedding_model_id, :vector) "
                    "ON CONFLICT(chunk_id) DO UPDATE SET "
                    "workspace_id = excluded.workspace_id, "
                    "embedding_model_id = excluded.embedding_model_id, "
                    "vector = excluded.vector"
                ),
                {
                    "chunk_id": chunk_id,
                    "workspace_id": workspace_id,
                    "embedding_model_id": model_id,
                    "vector": json.dumps(vector),
                },
            )
            session.commit()

    async def search(
        self,
        query: str,
        *,
        workspace_id: int,
        top_k: int,
    ) -> list[RetrievedChunk]:
        if self.embedding_provider is None:
            return []
        vector = await self.embed_query(query)
        with self.session_factory() as session:
            self._ensure_vector_table(session)
            rows = session.execute(
                text(
                    f"SELECT v.chunk_id, v.workspace_id, v.distance, c.text, wf.id AS workspace_file_id, wf.filename "
                    f"FROM {self.table_name} AS v "
                    "JOIN chunks AS c ON c.id = v.chunk_id "
                    "JOIN document_processing AS dp ON dp.id = c.document_processing_id "
                    "JOIN workspace_files AS wf ON wf.id = dp.workspace_file_id "
                    "WHERE v.workspace_id = :workspace_id AND v.vector MATCH :vector "
                    "ORDER BY v.distance ASC LIMIT :limit"
                ),
                {"workspace_id": workspace_id, "vector": json.dumps(vector), "limit": top_k},
            ).all()
            result: list[RetrievedChunk] = []
            for row in rows:
                result.append(
                    RetrievedChunk(
                        chunk_id=row.chunk_id,
                        workspace_file_id=row.workspace_file_id,
                        filename=row.filename,
                        text=row.text,
                        score=float(row.distance),
                    )
                )
            return result

    def _ensure_vector_table(self, session: Session, embedding_model_id: str | None = None) -> None:
        session.execute(
            text(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS {self.table_name} USING vec0("
                "chunk_id INTEGER PRIMARY KEY, "
                "workspace_id INTEGER, "
                "embedding_model_id TEXT, "
                "vector float[{self.dimension}]"
                ")"
            )
        )
        if embedding_model_id is not None:
            session.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_workspace_model "
                    f"ON {self.table_name}(workspace_id, embedding_model_id)"
                )
            )
