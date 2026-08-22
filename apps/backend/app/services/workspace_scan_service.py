"""Business service for workspace scanning, overview, and file queries."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.repositories import WorkspaceRepository
from app.db.workspace_file_repository import WorkspaceFileRepository
from app.schemas.workspace_scan import (
    DocumentItemResponse,
    DocumentListResponse,
    DocumentSummaryResponse,
    ScanJobResponse,
    WorkspaceFileListResponse,
    WorkspaceFileResponse,
    WorkspaceOverviewResponse,
)
from app.workers.scan_runner import ScanManager


class WorkspaceScanService:
    def __init__(
        self,
        workspace_repository: WorkspaceRepository | None = None,
        file_repository: WorkspaceFileRepository | None = None,
    ) -> None:
        self.workspace_repository = workspace_repository or WorkspaceRepository()
        self.file_repository = file_repository or WorkspaceFileRepository()

    def _get_required_workspace(self, session: Session):
        workspace = self.workspace_repository.get_current(session)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No workspace is selected",
            )
        return workspace

    async def trigger_scan(self, session: Session, scan_manager: ScanManager) -> ScanJobResponse:
        workspace = self._get_required_workspace(session)
        job = await scan_manager.start_scan(workspace.id)
        return ScanJobResponse.model_validate(job)

    def get_latest_scan(self, session: Session) -> ScanJobResponse | None:
        workspace = self._get_required_workspace(session)
        job = self.file_repository.get_latest_scan_job(session, workspace.id)
        if not job:
            return None
        return ScanJobResponse.model_validate(job)

    async def cancel_scan(self, session: Session, scan_manager: ScanManager) -> dict[str, bool]:
        workspace = self._get_required_workspace(session)
        cancelled = await scan_manager.cancel_scan(workspace.id)
        return {"cancelled": cancelled}

    def get_overview(self, session: Session) -> WorkspaceOverviewResponse:
        workspace = self._get_required_workspace(session)
        stats = self.file_repository.get_overview_stats(session, workspace.id)
        latest_job = self.file_repository.get_latest_scan_job(session, workspace.id)

        recent_files_resp = [WorkspaceFileResponse.model_validate(f) for f in stats["recent_files"]]
        latest_scan_resp = ScanJobResponse.model_validate(latest_job) if latest_job else None

        return WorkspaceOverviewResponse(
            workspace_id=workspace.id,
            total_files=stats["total_files"],
            total_size_bytes=stats["total_size_bytes"],
            files_by_category=stats["files_by_category"],
            files_by_status=stats["files_by_status"],
            pending_changes_count=stats["pending_changes_count"],
            recent_files=recent_files_resp,
            latest_scan=latest_scan_resp,
        )

    def list_files(
        self,
        session: Session,
        *,
        category: str | None = None,
        fs_status: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> WorkspaceFileListResponse:
        workspace = self._get_required_workspace(session)
        items, total = self.file_repository.list_files(
            session,
            workspace.id,
            category=category,
            fs_status=fs_status,
            search=search,
            offset=offset,
            limit=limit,
        )
        item_responses = [WorkspaceFileResponse.model_validate(item) for item in items]
        return WorkspaceFileListResponse(
            items=item_responses,
            total=total,
            offset=offset,
            limit=limit,
        )

    def get_document_summary(self, session: Session) -> DocumentSummaryResponse:
        workspace = self._get_required_workspace(session)
        counts = self.file_repository.get_document_summary_counts(session, workspace.id)
        return DocumentSummaryResponse(**counts)

    def list_documents(
        self,
        session: Session,
        *,
        document_status: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> DocumentListResponse:
        workspace = self._get_required_workspace(session)
        items, total = self.file_repository.list_documents(
            session,
            workspace.id,
            document_status=document_status,
            search=search,
            offset=offset,
            limit=limit,
        )
        item_responses = [DocumentItemResponse.model_validate(item) for item in items]
        return DocumentListResponse(
            items=item_responses,
            total=total,
            offset=offset,
            limit=limit,
        )
