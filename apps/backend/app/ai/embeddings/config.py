"""Centralized embedding configuration — single source of truth for active model settings."""

import hashlib

# Active embedding model settings. All application code must import from here;
# do not hardcode model names or dimensions elsewhere.
ACTIVE_EMBEDDING_MODEL_NAME = "nomic-embed-text"
ACTIVE_EMBEDDING_DIMENSION = 768
ACTIVE_EMBEDDING_NORMALIZE = True

# Default batch size for embedding sync (overridable via Settings.embedding_batch_size).
DEFAULT_EMBEDDING_BATCH_SIZE = 32

# Maximum automatic retry attempts before a chunk embedding stays failed.
MAX_EMBEDDING_ATTEMPTS = 3


def get_active_embedding_model_id() -> str:
    """Derive a stable identifier from the active embedding configuration."""
    norm_flag = "1" if ACTIVE_EMBEDDING_NORMALIZE else "0"
    raw = f"{ACTIVE_EMBEDDING_MODEL_NAME}|{ACTIVE_EMBEDDING_DIMENSION}|{norm_flag}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{ACTIVE_EMBEDDING_MODEL_NAME}@{ACTIVE_EMBEDDING_DIMENSION}@{digest}"
