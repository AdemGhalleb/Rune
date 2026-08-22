"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.embeddings.config import ACTIVE_EMBEDDING_MODEL_NAME
from app.ai.providers.ollama import OllamaEmbeddingProvider
from app.api.v1.router import router as v1_router
from app.core.config import Settings, get_settings
from app.core.logging import setup_logging
from app.db.database import create_database_engine, create_session_factory, run_migrations
from app.db.models import Message, MessageStatus
from app.db.vector_store import SQLiteChunkVectorStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    run_migrations(settings)
    app.state.engine = create_database_engine(settings)
    app.state.session_factory = create_session_factory(app.state.engine)
    app.state.vector_store = SQLiteChunkVectorStore(
        app.state.session_factory,
        OllamaEmbeddingProvider(settings.ollama_base_url, ACTIVE_EMBEDDING_MODEL_NAME),
    )
    with app.state.session_factory() as session:
        session.query(Message).filter(Message.status == MessageStatus.STREAMING.value).update(
            {Message.status: MessageStatus.FAILED.value, Message.error: "generation interrupted"},
            synchronize_session=False,
        )
        session.commit()
    logger.info(
        "Starting %s v%s on http://%s:%s",
        settings.app_name,
        settings.app_version,
        settings.host,
        settings.port,
    )
    yield
    app.state.engine.dispose()
    logger.info("Shutting down %s", settings.app_name)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging("DEBUG" if settings.debug else "INFO")

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.state.settings = settings

    # Local dev: allow the Vite dev server to call the backend.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:1420",
            "http://127.0.0.1:1420",
            "tauri://localhost",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router)

    return app
