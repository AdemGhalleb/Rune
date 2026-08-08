"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import health, workspace

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(workspace.router)
