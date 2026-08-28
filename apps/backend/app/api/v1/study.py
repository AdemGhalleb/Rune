"""Study generation and persistence API endpoints (Phase 5A & 5B)."""

import logging
from collections.abc import Generator

from fastapi import APIRouter, HTTPException, Query, Request, status
from sqlalchemy.orm import Session, sessionmaker

from app.ai.providers.base import LLMProviderError, LLMProviderUnavailable
from app.ai.providers.ollama import OllamaProvider
from app.core.config import Settings
from app.db.database import get_session
from app.schemas.study import (
    ExplanationRequest,
    ExplanationResponse,
    FlashcardItemPersisted,
    FlashcardReviewUpdate,
    FlashcardSetResponse,
    FlashcardsRequest,
    QuizAttemptCreate,
    QuizAttemptResponse,
    QuizRequest,
    QuizResponse,
    StudySessionCreate,
    StudySessionDetail,
    StudySessionSummary,
    SummaryRequest,
    SummaryResponse,
)
from app.services.retrieval import RetrievalService
from app.services.study_generation import (
    InsufficientContextError,
    StudyGenerationError,
    StudyGenerationService,
)
from app.services.study_persistence import StudyPersistenceService
from app.services.workspace import WorkspaceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/study", tags=["study"])


def get_db_session(request: Request) -> Generator[Session, None, None]:
    yield from get_session(request.app.state.session_factory)


def _provider(request: Request) -> OllamaProvider:
    provider = getattr(request.app.state, "ollama_provider", None)
    if provider is None:
        settings: Settings = request.app.state.settings
        provider = OllamaProvider(settings.ollama_base_url, settings.ollama_model)
        request.app.state.ollama_provider = provider
    return provider


def _get_service(request: Request) -> StudyGenerationService:
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        workspace = WorkspaceService().get_current(session)
        if workspace is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active workspace found. Please select a workspace first.",
            )
        workspace_id = workspace.id

    retrieval = RetrievalService(
        getattr(request.app.state, "vector_store", None),
        workspace_id=workspace_id,
    )
    provider = _provider(request)
    settings: Settings = request.app.state.settings
    return StudyGenerationService(retrieval=retrieval, provider=provider, settings=settings)


def _get_persistence_service(session: Session) -> StudyPersistenceService:
    workspace = WorkspaceService().get_current(session)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active workspace found. Please select a workspace first.",
        )
    return StudyPersistenceService(session=session, workspace_id=workspace.id)


# --- Phase 5A: Generation Endpoints ---


@router.post(
    "/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a grounded summary",
)
async def generate_summary(
    payload: SummaryRequest,
    request: Request,
) -> SummaryResponse:
    service = _get_service(request)
    try:
        return await service.generate_summary(
            topic=payload.topic,
            workspace_file_id=payload.workspace_file_id,
        )
    except LLMProviderUnavailable as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama is unavailable: {err}",
        ) from err
    except InsufficientContextError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        ) from err
    except (LLMProviderError, StudyGenerationError) as err:
        logger.exception("Summary generation failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Study generation failed: {err}",
        ) from err


@router.post(
    "/flashcards",
    response_model=FlashcardSetResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate grounded flashcards",
)
async def generate_flashcards(
    payload: FlashcardsRequest,
    request: Request,
) -> FlashcardSetResponse:
    service = _get_service(request)
    try:
        return await service.generate_flashcards(
            topic=payload.topic,
            workspace_file_id=payload.workspace_file_id,
            count=payload.count,
        )
    except LLMProviderUnavailable as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama is unavailable: {err}",
        ) from err
    except InsufficientContextError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        ) from err
    except (LLMProviderError, StudyGenerationError) as err:
        logger.exception("Flashcards generation failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Study generation failed: {err}",
        ) from err


@router.post(
    "/quiz",
    response_model=QuizResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a grounded multiple-choice quiz",
)
async def generate_quiz(
    payload: QuizRequest,
    request: Request,
) -> QuizResponse:
    service = _get_service(request)
    try:
        return await service.generate_quiz(
            topic=payload.topic,
            workspace_file_id=payload.workspace_file_id,
            count=payload.count,
        )
    except LLMProviderUnavailable as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama is unavailable: {err}",
        ) from err
    except InsufficientContextError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        ) from err
    except (LLMProviderError, StudyGenerationError) as err:
        logger.exception("Quiz generation failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Study generation failed: {err}",
        ) from err


@router.post(
    "/explain",
    response_model=ExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a grounded concept explanation",
)
async def generate_explanation(
    payload: ExplanationRequest,
    request: Request,
) -> ExplanationResponse:
    service = _get_service(request)
    try:
        return await service.generate_explanation(
            topic=payload.topic,
            workspace_file_id=payload.workspace_file_id,
        )
    except LLMProviderUnavailable as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama is unavailable: {err}",
        ) from err
    except InsufficientContextError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        ) from err
    except (LLMProviderError, StudyGenerationError) as err:
        logger.exception("Explanation generation failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Study generation failed: {err}",
        ) from err


# --- Phase 5B: Study Persistence Endpoints ---


@router.post(
    "/sessions",
    response_model=StudySessionDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a persistent study session",
)
async def create_study_session(
    payload: StudySessionCreate,
    request: Request,
) -> StudySessionDetail:
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        service = _get_persistence_service(session)
        return service.create_session(payload)


@router.get(
    "/sessions",
    response_model=list[StudySessionSummary],
    status_code=status.HTTP_200_OK,
    summary="List persistent study sessions in the active workspace",
)
async def list_study_sessions(
    request: Request,
    session_type: str | None = Query(default=None),
    workspace_file_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[StudySessionSummary]:
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        service = _get_persistence_service(session)
        return service.list_sessions(
            session_type=session_type,
            workspace_file_id=workspace_file_id,
            limit=limit,
            offset=offset,
        )


@router.get(
    "/sessions/{session_id}",
    response_model=StudySessionDetail,
    status_code=status.HTTP_200_OK,
    summary="Get full study session details",
)
async def get_study_session(
    session_id: int,
    request: Request,
) -> StudySessionDetail:
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        service = _get_persistence_service(session)
        detail = service.get_session(session_id)
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Study session {session_id} not found",
            )
        return detail


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a study session",
)
async def delete_study_session(
    session_id: int,
    request: Request,
) -> None:
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        service = _get_persistence_service(session)
        deleted = service.delete_session(session_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Study session {session_id} not found",
            )


@router.post(
    "/sessions/{session_id}/flashcards/{card_id}/review",
    response_model=FlashcardItemPersisted,
    status_code=status.HTTP_200_OK,
    summary="Update review state on a flashcard",
)
async def review_flashcard(
    session_id: int,
    card_id: int,
    payload: FlashcardReviewUpdate,
    request: Request,
) -> FlashcardItemPersisted:
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        service = _get_persistence_service(session)
        try:
            return service.update_flashcard_review(session_id, card_id, payload)
        except KeyError as err:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(err),
            ) from err


@router.post(
    "/sessions/{session_id}/quiz/attempt",
    response_model=QuizAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a quiz attempt",
)
async def record_quiz_attempt(
    session_id: int,
    payload: QuizAttemptCreate,
    request: Request,
) -> QuizAttemptResponse:
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        service = _get_persistence_service(session)
        try:
            return service.record_quiz_attempt(session_id, payload)
        except KeyError as err:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(err),
            ) from err


@router.get(
    "/sessions/{session_id}/quiz/attempts",
    response_model=list[QuizAttemptResponse],
    status_code=status.HTTP_200_OK,
    summary="Get attempt history for a quiz session",
)
async def get_quiz_attempts(
    session_id: int,
    request: Request,
) -> list[QuizAttemptResponse]:
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        service = _get_persistence_service(session)
        return service.get_quiz_attempts(session_id)
