"""Database repository for WorkspaceFile, DocumentProcessing, and ScanJob models."""

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Chunk,
    ChunkingStatus,
    DocumentProcessing,
    DocumentSegment,
    ExtractionStatus,
    FsStatus,
    ScanJob,
    ScanJobStatus,
    WorkspaceFile,
)


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
            started_at=datetime.now(UTC),
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
            terminal_statuses = (
                ScanJobStatus.COMPLETED.value,
                ScanJobStatus.FAILED.value,
                ScanJobStatus.CANCELLED.value,
            )
            if status in terminal_statuses:
                job.finished_at = datetime.now(UTC)
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
        pending_changes = (
            by_status.get(FsStatus.NEW.value, 0) + by_status.get(FsStatus.MODIFIED.value, 0)
        )

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
        count_stmt = select(func.count(WorkspaceFile.id)).where(
            WorkspaceFile.workspace_id == workspace_id
        )

        if category:
            stmt = stmt.where(WorkspaceFile.category == category)
            count_stmt = count_stmt.where(WorkspaceFile.category == category)
        if fs_status:
            stmt = stmt.where(WorkspaceFile.fs_status == fs_status)
            count_stmt = count_stmt.where(WorkspaceFile.fs_status == fs_status)
        if search:
            pattern = f"%{search.strip()}%"
            search_filter = WorkspaceFile.filename.ilike(
                pattern
            ) | WorkspaceFile.relative_path.ilike(pattern)
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        total_count = session.scalar(count_stmt) or 0
        ordered_stmt = stmt.order_by(WorkspaceFile.relative_path.asc()).offset(offset).limit(limit)
        items = session.scalars(ordered_stmt).all()
        return items, total_count

    # -------------------------------------------------------------------------
    # Document Ingestion Repository Operations
    # -------------------------------------------------------------------------

    def get_or_create_document_processing(
        self, session: Session, workspace_file: WorkspaceFile
    ) -> DocumentProcessing:
        """Fetch or create DocumentProcessing row for a WorkspaceFile."""
        stmt = select(DocumentProcessing).where(
            DocumentProcessing.workspace_file_id == workspace_file.id
        )
        doc_proc = session.scalar(stmt)
        if not doc_proc:
            doc_proc = DocumentProcessing(
                workspace_file_id=workspace_file.id,
                extraction_status=ExtractionStatus.UNPROCESSED.value,
                chunking_status=ChunkingStatus.NOT_CHUNKED.value,
                source_content_hash=workspace_file.content_hash,
            )
            session.add(doc_proc)
            session.flush()
        return doc_proc

    def get_document_processing_by_file_id(
        self, session: Session, workspace_file_id: int
    ) -> DocumentProcessing | None:
        stmt = select(DocumentProcessing).where(
            DocumentProcessing.workspace_file_id == workspace_file_id
        )
        return session.scalar(stmt)

    def delete_segments_and_chunks_for_doc(self, session: Session, doc_processing_id: int) -> None:
        """DELETE-then-REINSERT helper: delete all chunks and segments for document."""
        session.query(Chunk).filter(Chunk.document_processing_id == doc_processing_id).delete(
            synchronize_session=False
        )
        session.query(DocumentSegment).filter(
            DocumentSegment.document_processing_id == doc_processing_id
        ).delete(synchronize_session=False)

    def delete_chunks_for_doc(self, session: Session, doc_processing_id: int) -> None:
        """DELETE-then-REINSERT helper: delete all chunks for document."""
        session.query(Chunk).filter(Chunk.document_processing_id == doc_processing_id).delete(
            synchronize_session=False
        )

    def reconcile_orphaned_doc_processing_states(
        self, session: Session, workspace_id: int
    ) -> int:
        """Reset abandoned in-flight document rows to retryable states."""
        stmt = (
            select(DocumentProcessing)
            .join(WorkspaceFile)
            .where(
                WorkspaceFile.workspace_id == workspace_id,
                (DocumentProcessing.extraction_status == ExtractionStatus.EXTRACTING.value)
                | (DocumentProcessing.chunking_status == ChunkingStatus.CHUNKING.value),
            )
        )
        orphans = list(session.scalars(stmt).all())
        count = 0
        for doc in orphans:
            if doc.extraction_status == ExtractionStatus.EXTRACTING.value:
                doc.extraction_status = ExtractionStatus.UNPROCESSED.value
                doc.extraction_error_message = None
                count += 1
            if doc.chunking_status == ChunkingStatus.CHUNKING.value:
                doc.chunking_status = ChunkingStatus.NOT_CHUNKED.value
                doc.chunking_error_message = None
                count += 1
        if count > 0:
            session.commit()
        return count

    @staticmethod
    def derive_document_status(doc_proc: DocumentProcessing | None) -> str:
        """Map a document row to the four UX states used by the desktop app."""
        if doc_proc is None:
            return "not_started"

        e_stat = doc_proc.extraction_status
        c_stat = doc_proc.chunking_status

        if e_stat == ExtractionStatus.EXTRACTING.value or c_stat == ChunkingStatus.CHUNKING.value:
            return "processing"
        if e_stat == ExtractionStatus.FAILED.value or c_stat == ChunkingStatus.FAILED.value:
            return "failed"
        if e_stat == ExtractionStatus.EXTRACTED.value and c_stat == ChunkingStatus.CHUNKED.value:
            return "ready"
        return "not_started"

    def get_document_summary_counts(self, session: Session, workspace_id: int) -> dict[str, int]:
        """Compute live document state counts for UX banner at scale."""
        supported_exts = (".pdf", ".docx", ".txt", ".md")
        stmt = (
            select(DocumentProcessing)
            .join(WorkspaceFile)
            .where(
                WorkspaceFile.workspace_id == workspace_id,
                WorkspaceFile.fs_status.notin_([FsStatus.DELETED.value, FsStatus.IGNORED.value]),
                func.lower(WorkspaceFile.extension).in_(supported_exts),
            )
        )
        docs = list(session.scalars(stmt).all())

        counts = {
            "not_started": 0,
            "processing": 0,
            "ready": 0,
            "failed": 0,
            "total_supported": len(docs),
        }

        for d in docs:
            status = self.derive_document_status(d)
            counts[status] += 1

        return counts

    def list_documents(
        self,
        session: Session,
        workspace_id: int,
        *,
        document_status: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[dict], int]:
        """Return supported documents with their live ingestion status."""
        supported_exts = (".pdf", ".docx", ".txt", ".md")
        stmt = (
            select(WorkspaceFile, DocumentProcessing)
            .outerjoin(DocumentProcessing, DocumentProcessing.workspace_file_id == WorkspaceFile.id)
            .where(
                WorkspaceFile.workspace_id == workspace_id,
                WorkspaceFile.fs_status.notin_([FsStatus.DELETED.value, FsStatus.IGNORED.value]),
                func.lower(WorkspaceFile.extension).in_(supported_exts),
            )
            .order_by(WorkspaceFile.relative_path.asc())
        )

        rows = list(session.execute(stmt).all())
        items: list[dict] = []

        for file_rec, doc_proc in rows:
            derived_status = self.derive_document_status(doc_proc)
            if document_status and derived_status != document_status:
                continue
            if search and not (
                search.lower() in file_rec.filename.lower()
                or search.lower() in file_rec.relative_path.lower()
            ):
                continue

            items.append(
                {
                    "id": file_rec.id,
                    "workspace_file_id": file_rec.id,
                    "filename": file_rec.filename,
                    "relative_path": file_rec.relative_path,
                    "extension": file_rec.extension,
                    "category": file_rec.category,
                    "size_bytes": file_rec.size_bytes,
                    "fs_status": file_rec.fs_status,
                    "modified_at": file_rec.modified_at,
                    "extraction_status": doc_proc.extraction_status if doc_proc else "unprocessed",
                    "chunking_status": doc_proc.chunking_status if doc_proc else "not_chunked",
                    "document_status": derived_status,
                }
            )

        total = len(items)
        return items[offset : offset + limit], total

