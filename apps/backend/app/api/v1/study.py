import logging
from collections.abc import Generator

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy.orm import Session, sessionmaker

from app.ai.providers.base import LLMProviderError, LLMProviderUnavailable
from app.ai.providers.ollama import OllamaProvider
from app.core.config import Settings
from app.db.database import get_session
from app.schemas.study import (
    ExplanationRequest,
    ExplanationResponse,
    FlashcardSetResponse,
    FlashcardsRequest,
    QuizRequest,
    QuizResponse,
    SummaryRequest,
    SummaryResponse,
)
from app.services.retrieval import RetrievalService
from app.services.study_generation import (
    InsufficientContextError,
    StudyGenerationError,
    StudyGenerationService,
)
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
