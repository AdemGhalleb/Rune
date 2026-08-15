from sqlalchemy import inspect


def test_chunk_embeddings_schema_has_required_columns_and_indices(session_factory):
    inspector = inspect(session_factory.kw["bind"])
    columns = {column["name"] for column in inspector.get_columns("chunk_embeddings")}
    assert columns == {
        "chunk_id",
        "workspace_id",
        "embedding_model_id",
        "status",
        "content_hash_at_embedding",
        "error_code",
        "error_message",
        "attempt_count",
        "created_at",
        "updated_at",
    }
    indexes = {index["name"] for index in inspector.get_indexes("chunk_embeddings")}
    assert {"ix_chunk_embeddings_workspace_status", "ix_chunk_embeddings_model_id"} <= indexes
