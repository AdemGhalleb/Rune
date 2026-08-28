"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import chat, health, study, workspace

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(chat.router)
router.include_router(workspace.router)
router.include_router(study.router)
