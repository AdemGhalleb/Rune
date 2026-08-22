"""Thin conversation and streamed-chat HTTP boundary."""

import json
import time
from collections.abc import AsyncIterator, Generator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.ai.providers.ollama import OllamaProvider
from app.core.config import Settings
from app.db.database import get_session
from app.db.models import (
    Conversation,
    Message,
    MessageRole,
    MessageSource,
    MessageStatus,
    WorkspaceFile,
)
from app.schemas.chat import (
    ConversationCreate,
    ConversationDetail,
    ConversationResponse,
    MessageCreate,
    SourceResponse,
)
from app.services.rag import RagService
from app.services.retrieval import RetrievalService
from app.services.workspace import WorkspaceService

router = APIRouter(tags=["chat"])


def get_db_session(request: Request) -> Generator[Session, None, None]:
    yield from get_session(request.app.state.session_factory)


def _provider(request: Request) -> OllamaProvider:
    provider = getattr(request.app.state, "ollama_provider", None)
    if provider is None:
        settings: Settings = request.app.state.settings
        provider = OllamaProvider(settings.ollama_base_url, settings.ollama_model)
        request.app.state.ollama_provider = provider
    return provider


@router.get("/llm/status")
async def llm_status(request: Request) -> dict[str, object]:
    provider = _provider(request)
    return {"available": await provider.is_available(), "model": provider.model}


@router.post(
    "/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED
)
def create_conversation(
    payload: ConversationCreate, session: Session = Depends(get_db_session)
) -> Conversation:
    conversation = Conversation(title=payload.title)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(session: Session = Depends(get_db_session)) -> list[Conversation]:
    return list(
        session.scalars(select(Conversation).order_by(Conversation.updated_at.desc())).all()
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int, session: Session = Depends(get_db_session)
) -> Conversation:
    conversation = session.scalar(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/messages/{message_id}/sources", response_model=list[SourceResponse])
def get_message_sources(
    message_id: int, session: Session = Depends(get_db_session)
) -> list[SourceResponse]:
    rows = session.execute(
        select(MessageSource, WorkspaceFile.filename)
        .join(WorkspaceFile, MessageSource.workspace_file_id == WorkspaceFile.id)
        .where(MessageSource.message_id == message_id)
        .order_by(MessageSource.rank)
    ).all()
    return [
        SourceResponse(
            id=s.id,
            chunk_id=s.chunk_id,
            workspace_file_id=s.workspace_file_id,
            filename=name,
            rank=s.rank,
            relevance_score=s.relevance_score,
        )
        for s, name in rows
    ]


def _sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: int, payload: MessageCreate, request: Request
) -> StreamingResponse:
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        conversation = session.get(Conversation, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        user = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER.value,
            content=payload.content,
            status=MessageStatus.COMPLETE.value,
        )
        assistant = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT.value,
            content="",
            status=MessageStatus.PENDING.value,
            model_used=_provider(request).model,
        )
        session.add_all([user, assistant])
        if not conversation.title:
            conversation.title = payload.content[:80]
        session.commit()
        assistant_id = assistant.id
        history = [
            (m.role, m.content)
            for m in session.scalars(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
            ).all()[:-1]
        ]

    with factory() as session:
        workspace = WorkspaceService().get_current(session)
    rag = RagService(
        RetrievalService(
            getattr(request.app.state, "vector_store", None),
            workspace_id=workspace.id if workspace else None,
        ),
        _provider(request),
        request.app.state.settings,
    )

    async def generate() -> AsyncIterator[str]:
        try:
            plan = await rag.prepare(payload.content, history)
            with factory() as session:
                message = session.get(Message, assistant_id)
                if message:
                    message.status = MessageStatus.STREAMING.value
                    session.commit()
            yield _sse("message", {"id": assistant_id, "status": "streaming"})
            content = ""
            last_save = time.monotonic()
            async for token in rag.stream(plan):
                if await request.is_disconnected():
                    with factory() as session:
                        message = session.get(Message, assistant_id)
                        if message:
                            message.content = content
                            message.status = MessageStatus.CANCELLED.value
                            session.commit()
                    return
                content += token
                yield _sse("token", {"id": assistant_id, "content": token})
                if time.monotonic() - last_save >= 1:
                    with factory() as session:
                        message = session.get(Message, assistant_id)
                        if message:
                            message.content = content
                            session.commit()
                    last_save = time.monotonic()
            with factory() as session:
                message = session.get(Message, assistant_id)
                if message:
                    message.content = content
                    message.status = MessageStatus.COMPLETE.value
                    for rank, chunk in enumerate(plan.sources, start=1):
                        session.add(
                            MessageSource(
                                message_id=message.id,
                                chunk_id=chunk.chunk_id,
                                workspace_file_id=chunk.workspace_file_id,
                                rank=rank,
                                relevance_score=chunk.score,
                            )
                        )
                    session.commit()
            yield _sse("complete", {"id": assistant_id})
        except Exception as err:
            # Persist a terminal, recoverable state even when a provider fails mid-stream.
            with factory() as session:
                message = session.get(Message, assistant_id)
                if message:
                    message.status = MessageStatus.FAILED.value
                    message.error = str(err)[:500]
                    session.commit()
            yield _sse("error", {"id": assistant_id, "error": str(err)[:500]})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
