"""Health check endpoint."""

from fastapi import APIRouter

from app.api.schemas import HealthResponse
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        app=settings.app_name,
    )
