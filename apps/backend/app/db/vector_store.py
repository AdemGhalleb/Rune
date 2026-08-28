"""Minimal sqlite-vec-backed chunk vector store for Phase 3 retrieval."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.ai.embeddings.config import ACTIVE_EMBEDDING_DIMENSION, get_active_embedding_model_id
from app.ai.providers.base import EmbeddingProvider
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
        return self._normalize(await self.embedding_provider.embed(query))

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
        normalized_vector = self._normalize(vector)
        with self.session_factory() as session:
            self._ensure_vector_table(session, model_id)
            # SQLite virtual tables do not implement ON CONFLICT / UPSERT.
            # Replacing a chunk vector is therefore an explicit delete + insert.
            session.execute(
                text(f"DELETE FROM {self.table_name} WHERE chunk_id = :chunk_id"),
                {"chunk_id": chunk_id},
            )
            session.execute(
                text(
                    f"INSERT INTO {self.table_name}("
                    "chunk_id, workspace_id, embedding_model_id, vector"
                    ") "
                    "VALUES (:chunk_id, :workspace_id, :embedding_model_id, :vector)"
                ),
                {
                    "chunk_id": chunk_id,
                    "workspace_id": workspace_id,
                    "embedding_model_id": model_id,
                    "vector": json.dumps(normalized_vector),
                },
            )
            session.commit()

    async def search(
        self,
        query: str,
        *,
        workspace_id: int,
        top_k: int,
        workspace_file_id: int | None = None,
    ) -> list[RetrievedChunk]:
        if self.embedding_provider is None:
            return []
        vector = await self.embed_query(query)
        with self.session_factory() as session:
            self._ensure_vector_table(session)
            file_filter = "AND wf.id = :workspace_file_id " if workspace_file_id is not None else ""
            params: dict[str, object] = {
                "workspace_id": workspace_id,
                "vector": json.dumps(vector),
                "limit": top_k,
            }
            if workspace_file_id is not None:
                params["workspace_file_id"] = workspace_file_id
            rows = session.execute(
                text(
                    "SELECT v.chunk_id, v.workspace_id, v.distance, c.text, "
                    "wf.id AS workspace_file_id, wf.filename "
                    f"FROM {self.table_name} AS v "
                    "JOIN chunks AS c ON c.id = v.chunk_id "
                    "JOIN document_processing AS dp ON dp.id = c.document_processing_id "
                    "JOIN workspace_files AS wf ON wf.id = dp.workspace_file_id "
                    f"WHERE v.workspace_id = :workspace_id {file_filter}AND v.vector MATCH :vector "
                    "AND v.k = :limit ORDER BY v.distance ASC"
                ),
                params,
            ).all()
            result: list[RetrievedChunk] = []
            for row in rows:
                result.append(
                    RetrievedChunk(
                        chunk_id=row.chunk_id,
                        workspace_file_id=row.workspace_file_id,
                        filename=row.filename,
                        text=row.text,
                        # Vectors are normalized on write/query. For normalized
                        # vectors, cosine similarity is 1 - (L2_distance² / 2).
                        score=max(0.0, 1.0 - (float(row.distance) ** 2 / 2.0)),
                    )
                )
            return result

    def get_chunks_for_file(
        self,
        *,
        workspace_id: int,
        workspace_file_id: int,
        limit: int = 20,
    ) -> list[RetrievedChunk]:
        with self.session_factory() as session:
            rows = session.execute(
                text(
                    "SELECT c.id AS chunk_id, c.text, "
                    "wf.id AS workspace_file_id, wf.filename "
                    "FROM chunks AS c "
                    "JOIN document_processing AS dp ON dp.id = c.document_processing_id "
                    "JOIN workspace_files AS wf ON wf.id = dp.workspace_file_id "
                    "WHERE wf.workspace_id = :workspace_id AND wf.id = :workspace_file_id "
                    "ORDER BY c.chunk_index ASC "
                    "LIMIT :limit"
                ),
                {
                    "workspace_id": workspace_id,
                    "workspace_file_id": workspace_file_id,
                    "limit": limit,
                },
            ).all()
            return [
                RetrievedChunk(
                    chunk_id=row.chunk_id,
                    workspace_file_id=row.workspace_file_id,
                    filename=row.filename,
                    text=row.text,
                    score=1.0,
                )
                for row in rows
            ]

    def _ensure_vector_table(self, session: Session, embedding_model_id: str | None = None) -> None:
        session.execute(
            text(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS {self.table_name} USING vec0("
                "chunk_id INTEGER PRIMARY KEY, "
                "workspace_id INTEGER, "
                "embedding_model_id TEXT, "
                f"vector float[{self.dimension}]"
                ")"
            )
        )

    @staticmethod
    def _normalize(vector: list[float]) -> list[float]:
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            raise ValueError("Embedding vector must not be all zeros")
        return [value / magnitude for value in vector]
