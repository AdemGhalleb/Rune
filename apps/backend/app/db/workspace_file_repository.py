"""Database repository for WorkspaceFile, DocumentProcessing, and ScanJob models."""

from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import DocumentProcessing, FsStatus, ScanJob, ScanJobStatus, WorkspaceFile


class WorkspaceFileRepository:
    """Persistence operations for workspace files and scan jobs."""

    def get_by_workspace(self, session: Session, workspace_id: int) -> list[WorkspaceFile]:
        """Fetch all workspace files for a given workspace."""
        stmt = select(WorkspaceFile).where(WorkspaceFile.workspace_id == workspace_id)
        return list(session.scalars(stmt).all())

    def get_by_relative_path(
        self, session: Session, workspace_id: int, relative_path: str
    ) -> WorkspaceFile | None:
        stmt = select(WorkspaceFile).where(
            WorkspaceFile.workspace_id == workspace_id,
            WorkspaceFile.relative_path == relative_path,
        )
        return session.scalar(stmt)

    def create_scan_job(self, session: Session, workspace_id: int) -> ScanJob:
        job = ScanJob(
            workspace_id=workspace_id,
            status=ScanJobStatus.RUNNING.value,
            started_at=datetime.now(timezone.utc),
            files_discovered=0,
            files_processed=0,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return job

    def get_latest_scan_job(self, session: Session, workspace_id: int) -> ScanJob | None:
        stmt = (
            select(ScanJob)
            .where(ScanJob.workspace_id == workspace_id)
            .order_by(ScanJob.id.desc())
            .limit(1)
        )
        return session.scalar(stmt)

    def update_scan_job_progress(
        self,
        session: Session,
        job_id: int,
        *,
        files_discovered: int | None = None,
        files_processed: int | None = None,
        status: str | None = None,
        error: str | None = None,
    ) -> None:
        job = session.get(ScanJob, job_id)
        if not job:
            return
        if files_discovered is not None:
            job.files_discovered = files_discovered
        if files_processed is not None:
            job.files_processed = files_processed
        if status is not None:
            job.status = status
            if status in (ScanJobStatus.COMPLETED.value, ScanJobStatus.FAILED.value, ScanJobStatus.CANCELLED.value):
                job.finished_at = datetime.now(timezone.utc)
        if error is not None:
            job.error = error
        session.commit()

    def get_overview_stats(self, session: Session, workspace_id: int) -> dict:
        """Aggregate summary metrics for a workspace."""
        total_files = (
            session.scalar(
                select(func.count(WorkspaceFile.id)).where(
                    WorkspaceFile.workspace_id == workspace_id,
                    WorkspaceFile.fs_status != FsStatus.DELETED.value,
                    WorkspaceFile.fs_status != FsStatus.IGNORED.value,
                )
            )
            or 0
        )

        total_bytes = (
            session.scalar(
                select(func.sum(WorkspaceFile.size_bytes)).where(
                    WorkspaceFile.workspace_id == workspace_id,
                    WorkspaceFile.fs_status != FsStatus.DELETED.value,
                    WorkspaceFile.fs_status != FsStatus.IGNORED.value,
                )
            )
            or 0
        )

        # Count by category (excluding deleted/ignored)
        cat_stmt = (
            select(WorkspaceFile.category, func.count(WorkspaceFile.id))
            .where(
                WorkspaceFile.workspace_id == workspace_id,
                WorkspaceFile.fs_status != FsStatus.DELETED.value,
                WorkspaceFile.fs_status != FsStatus.IGNORED.value,
            )
            .group_by(WorkspaceFile.category)
        )
        by_category = {cat: count for cat, count in session.execute(cat_stmt).all()}

        # Count by fs_status
        status_stmt = (
            select(WorkspaceFile.fs_status, func.count(WorkspaceFile.id))
            .where(WorkspaceFile.workspace_id == workspace_id)
            .group_by(WorkspaceFile.fs_status)
        )
        by_status = {st: count for st, count in session.execute(status_stmt).all()}

        # Pending changes (new + modified)
        pending_changes = by_status.get(FsStatus.NEW.value, 0) + by_status.get(FsStatus.MODIFIED.value, 0)

        # Recently modified files (top 5)
        recent_stmt = (
            select(WorkspaceFile)
            .where(
                WorkspaceFile.workspace_id == workspace_id,
                WorkspaceFile.fs_status != FsStatus.DELETED.value,
                WorkspaceFile.fs_status != FsStatus.IGNORED.value,
            )
            .order_by(WorkspaceFile.modified_at.desc())
            .limit(5)
        )
        recent_files = list(session.scalars(recent_stmt).all())

        return {
            "workspace_id": workspace_id,
            "total_files": total_files,
            "total_size_bytes": total_bytes,
            "files_by_category": by_category,
            "files_by_status": by_status,
            "pending_changes_count": pending_changes,
            "recent_files": recent_files,
        }

    def list_files(
        self,
        session: Session,
        workspace_id: int,
        *,
        category: str | None = None,
        fs_status: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[WorkspaceFile], int]:
        stmt = select(WorkspaceFile).where(WorkspaceFile.workspace_id == workspace_id)
        count_stmt = select(func.count(WorkspaceFile.id)).where(WorkspaceFile.workspace_id == workspace_id)

        if category:
            stmt = stmt.where(WorkspaceFile.category == category)
            count_stmt = count_stmt.where(WorkspaceFile.category == category)
        if fs_status:
            stmt = stmt.where(WorkspaceFile.fs_status == fs_status)
            count_stmt = count_stmt.where(WorkspaceFile.fs_status == fs_status)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(WorkspaceFile.filename.ilike(pattern) | WorkspaceFile.relative_path.ilike(pattern))
            count_stmt = count_stmt.where(
                WorkspaceFile.filename.ilike(pattern) | WorkspaceFile.relative_path.ilike(pattern)
            )

        total_count = session.scalar(count_stmt) or 0
        items = session.scalars(stmt.order_by(WorkspaceFile.relative_path.asc()).offset(offset).limit(limit)).all()
        return items, total_count
