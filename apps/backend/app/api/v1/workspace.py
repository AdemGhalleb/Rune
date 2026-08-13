"""Workspace management and scanning API endpoints."""

from collections.abc import Generator

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session, sessionmaker

from app.db.database import get_session
from app.schemas.workspace import WorkspaceResponse, WorkspaceSetRequest, WorkspaceUpdateRequest
from app.schemas.workspace_scan import (
    DocumentListResponse,
    DocumentSummaryResponse,
    ScanJobResponse,
    WorkspaceFileListResponse,
    WorkspaceOverviewResponse,
)
from app.services.workspace import WorkspaceService
from app.services.workspace_scan_service import WorkspaceScanService
from app.workers.scan_runner import ScanManager

router = APIRouter(prefix="/workspace", tags=["workspace"])


def get_db_session(request: Request) -> Generator[Session, None, None]:
    session_factory: sessionmaker[Session] = request.app.state.session_factory
    yield from get_session(session_factory)


def get_scan_manager(request: Request) -> ScanManager:
    scan_mgr = getattr(request.app.state, "scan_manager", None)
    if scan_mgr is None:
        session_factory = request.app.state.session_factory
        scan_mgr = ScanManager(session_factory)
        request.app.state.scan_manager = scan_mgr
    return scan_mgr


@router.get("", response_model=WorkspaceResponse | None)
def get_workspace(session: Session = Depends(get_db_session)) -> WorkspaceResponse | None:
    return WorkspaceService().get_current(session)


@router.put("", response_model=WorkspaceResponse, status_code=status.HTTP_200_OK)
def set_workspace(
    payload: WorkspaceSetRequest, session: Session = Depends(get_db_session)
) -> WorkspaceResponse:
    return WorkspaceService().set_current(session, root_path=payload.root_path, name=payload.name)


@router.patch("", response_model=WorkspaceResponse)
def update_workspace(
    payload: WorkspaceUpdateRequest, session: Session = Depends(get_db_session)
) -> WorkspaceResponse:
    return WorkspaceService().update_current(
        session, root_path=payload.root_path, name=payload.name
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def remove_workspace(session: Session = Depends(get_db_session)) -> Response:
    WorkspaceService().remove_current(session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/scan", response_model=ScanJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_workspace_scan(
    session: Session = Depends(get_db_session),
    scan_manager: ScanManager = Depends(get_scan_manager),
) -> ScanJobResponse:
    return await WorkspaceScanService().trigger_scan(session, scan_manager)


@router.get("/scan/latest", response_model=ScanJobResponse | None)
def get_latest_scan(
    session: Session = Depends(get_db_session),
) -> ScanJobResponse | None:
    return WorkspaceScanService().get_latest_scan(session)


@router.post("/scan/cancel")
async def cancel_workspace_scan(
    session: Session = Depends(get_db_session),
    scan_manager: ScanManager = Depends(get_scan_manager),
) -> dict[str, bool]:
    return await WorkspaceScanService().cancel_scan(session, scan_manager)


@router.get("/overview", response_model=WorkspaceOverviewResponse)
def get_workspace_overview(
    session: Session = Depends(get_db_session),
) -> WorkspaceOverviewResponse:
    return WorkspaceScanService().get_overview(session)


@router.get("/files", response_model=WorkspaceFileListResponse)
def list_workspace_files(
    category: str | None = Query(default=None),
    fs_status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    session: Session = Depends(get_db_session),
) -> WorkspaceFileListResponse:
    return WorkspaceScanService().list_files(
        session,
        category=category,
        fs_status=fs_status,
        search=search,
        offset=offset,
        limit=limit,
    )


@router.get("/documents/summary", response_model=DocumentSummaryResponse)
def get_document_summary(
    session: Session = Depends(get_db_session),
) -> DocumentSummaryResponse:
    return WorkspaceScanService().get_document_summary(session)


@router.get("/documents", response_model=DocumentListResponse)
def list_workspace_documents(
    document_status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    session: Session = Depends(get_db_session),
) -> DocumentListResponse:
    return WorkspaceScanService().list_documents(
        session,
        document_status=document_status,
        search=search,
        offset=offset,
        limit=limit,
    )
