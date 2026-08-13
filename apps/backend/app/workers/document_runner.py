"""In-process background document ingestion worker and pipeline runner."""

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from app.ai.chunking.fixed_chunker import (
    CURRENT_CHUNKER_NAME,
    CURRENT_CHUNKER_VERSION,
    FixedChunker,
)
from app.ai.extraction.base import (
    sanitize_error_message,
    validate_workspace_path,
)
from app.ai.extraction.factory import (
    CURRENT_EXTRACTOR_NAME,
    CURRENT_EXTRACTOR_VERSION,
    get_extractor_for_file,
)
from app.ai.extraction.onedrive import is_onedrive_placeholder
from app.db.models import (
    Chunk,
    ChunkingStatus,
    DocProcessingJobStatus,
    DocumentProcessing,
    DocumentProcessingJob,
    DocumentSegment,
    ExtractionStatus,
    FsStatus,
    Workspace,
    WorkspaceFile,
)
from app.db.workspace_file_repository import WorkspaceFileRepository

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class DocumentIngestionManager:
    """Manages document extraction and chunking background tasks for Rune workspaces."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        concurrency_limit: int = 3,
    ) -> None:
        self.session_factory = session_factory
        self.repository = WorkspaceFileRepository()
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self._in_flight: set[int] = set()
        self._lock = asyncio.Lock()

    def reconcile_startup(self, workspace_id: int) -> int:
        """Run startup reconciliation for orphaned 'extracting'/'chunking' rows."""
        with self.session_factory() as session:
            count = self.repository.reconcile_orphaned_doc_processing_states(session, workspace_id)
            if count > 0:
                logger.info(
                    "Reconciled %d orphaned in-flight document processing rows for workspace %d",
                    count,
                    workspace_id,
                )
            return count

    async def enqueue_workspace_documents(
        self, workspace_id: int, *, force_retry: bool = False
    ) -> int:
        """Find pending/stale documents in workspace and enqueue background processing."""
        self.reconcile_startup(workspace_id)

        with self.session_factory() as session:
            workspace = session.get(Workspace, workspace_id)
            if not workspace:
                return 0
            root_path = Path(workspace.root_path)

            # Query candidate files
            files = self.repository.get_by_workspace(session, workspace_id)
            candidate_files: list[tuple[WorkspaceFile, DocumentProcessing]] = []

            for f in files:
                if f.fs_status in (
                    FsStatus.DELETED.value,
                    FsStatus.IGNORED.value,
                    FsStatus.ERROR.value,
                ):
                    continue
                ext = Path(f.filename).suffix.lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue

                doc_proc = self.repository.get_or_create_document_processing(session, f)
                candidate_files.append((f, doc_proc))

            session.commit()

            # Filter candidates that need processing
            to_process: list[tuple[int, int]] = []  # (workspace_file_id, doc_proc_id)
            async with self._lock:
                for file_rec, doc_proc in candidate_files:
                    if file_rec.id in self._in_flight:
                        continue

                    needs_ext = self.needs_extraction(doc_proc, file_rec)
                    needs_chk = self.needs_chunking(doc_proc, file_rec)

                    if not needs_ext and not needs_chk:
                        continue

                    # Failure cap check on auto-enqueue (unless force_retry is True)
                    if not force_retry:
                        if needs_ext and doc_proc.extraction_error_count >= 3:
                            continue
                        if needs_chk and doc_proc.chunking_error_count >= 3:
                            continue

                    self._in_flight.add(file_rec.id)
                    to_process.append((file_rec.id, doc_proc.id))

        if not to_process:
            return 0

        # Launch processing task off main loop
        asyncio.create_task(
            self._process_batch(workspace_id, root_path, to_process, force_retry=force_retry)
        )
        return len(to_process)

    async def retry_single_document(self, workspace_id: int, workspace_file_id: int) -> bool:
        """Trigger explicit retry for a single document."""
        async with self._lock:
            if workspace_file_id in self._in_flight:
                logger.info(
                    "Document file_id=%d already processing in-flight, skipping retry trigger",
                    workspace_file_id,
                )
                return False

        with self.session_factory() as session:
            workspace = session.get(Workspace, workspace_id)
            if not workspace:
                return False
            root_path = Path(workspace.root_path)

            file_rec = session.get(WorkspaceFile, workspace_file_id)
            if not file_rec or file_rec.workspace_id != workspace_id:
                return False

            doc_proc = self.repository.get_or_create_document_processing(session, file_rec)
            # Reset error counts on explicit manual retry
            doc_proc.extraction_error_count = 0
            doc_proc.chunking_error_count = 0
            doc_proc.extraction_error_message = None
            doc_proc.chunking_error_message = None
            session.commit()

            doc_proc_id = doc_proc.id

        async with self._lock:
            self._in_flight.add(workspace_file_id)

        asyncio.create_task(
            self._process_batch(
                workspace_id,
                root_path,
                [(workspace_file_id, doc_proc_id)],
                force_retry=True,
            )
        )
        return True

    def needs_extraction(self, doc_proc: DocumentProcessing, file_rec: WorkspaceFile) -> bool:
        """Predicate checking if document needs extraction stage."""
        if doc_proc.extraction_status in (
            ExtractionStatus.UNPROCESSED.value,
            ExtractionStatus.FAILED.value,
        ):
            return True
        if doc_proc.source_content_hash != file_rec.content_hash:
            return True
        if doc_proc.extractor_version != CURRENT_EXTRACTOR_VERSION:
            return True
        return False

    def needs_chunking(self, doc_proc: DocumentProcessing, file_rec: WorkspaceFile) -> bool:
        """Predicate checking if document needs chunking stage."""
        if self.needs_extraction(doc_proc, file_rec):
            return False
        if doc_proc.chunking_status in (
            ChunkingStatus.NOT_CHUNKED.value,
            ChunkingStatus.FAILED.value,
        ):
            return True
        if doc_proc.chunker_version != CURRENT_CHUNKER_VERSION:
            return True
        return False

    async def _process_batch(
        self,
        workspace_id: int,
        root_path: Path,
        items: list[tuple[int, int]],
        *,
        force_retry: bool = False,
    ) -> None:
        """Process a batch of documents with bounded concurrency."""
        # Record marker job row
        with self.session_factory() as session:
            job = DocumentProcessingJob(
                workspace_id=workspace_id,
                status=DocProcessingJobStatus.RUNNING.value,
                started_at=datetime.now(UTC),
            )
            session.add(job)
            session.commit()
            job_id = job.id

        try:
            tasks = [
                self._process_single_file(workspace_id, root_path, file_id, doc_id, force_retry)
                for file_id, doc_id in items
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

            with self.session_factory() as session:
                j = session.get(DocumentProcessingJob, job_id)
                if j:
                    j.status = DocProcessingJobStatus.COMPLETED.value
                    j.finished_at = datetime.now(UTC)
                    session.commit()

        except Exception as err:
            logger.exception("Batch processing job %d failed: %s", job_id, err)
            with self.session_factory() as session:
                j = session.get(DocumentProcessingJob, job_id)
                if j:
                    j.status = DocProcessingJobStatus.FAILED.value
                    j.finished_at = datetime.now(UTC)
                    session.commit()

    async def _process_single_file(
        self,
        workspace_id: int,
        root_path: Path,
        file_id: int,
        doc_proc_id: int,
        force_retry: bool,
    ) -> None:
        """Process extraction and chunking for a single file under semaphore limit."""
        async with self.semaphore:
            try:
                await asyncio.to_thread(
                    self._execute_file_pipeline,
                    workspace_id,
                    root_path,
                    file_id,
                    doc_proc_id,
                    force_retry,
                )
            except Exception as err:
                logger.exception("Error in background doc runner for file_id=%d: %s", file_id, err)
            finally:
                async with self._lock:
                    self._in_flight.discard(file_id)

    def _execute_file_pipeline(
        self,
        workspace_id: int,
        root_path: Path,
        file_id: int,
        doc_proc_id: int,
        force_retry: bool,
    ) -> None:
        """Synchronous file processing logic run in executor thread."""
        with self.session_factory() as session:
            file_rec = session.get(WorkspaceFile, file_id)
            doc_proc = session.get(DocumentProcessing, doc_proc_id)

            if not file_rec or not doc_proc:
                return

            abs_path = root_path / file_rec.relative_path

            # Security check: validate workspace boundary
            try:
                validate_workspace_path(abs_path, root_path)
            except Exception as err:
                doc_proc.extraction_status = ExtractionStatus.FAILED.value
                doc_proc.extraction_error_message = sanitize_error_message(err)
                doc_proc.extraction_error_count += 1
                session.commit()
                return

            # OneDrive placeholder check
            if is_onedrive_placeholder(abs_path):
                doc_proc.extraction_status = ExtractionStatus.FAILED.value
                doc_proc.extraction_error_message = "file not downloaded locally"
                doc_proc.extraction_error_count += 1
                doc_proc.extraction_attempted_at = datetime.now(UTC)
                session.commit()
                return

            # -----------------------------------------------------------------
            # Stage 1: Extraction (if needed)
            # -----------------------------------------------------------------
            needs_ext = self.needs_extraction(doc_proc, file_rec)

            if needs_ext:
                extractor = get_extractor_for_file(abs_path)
                if not extractor:
                    return

                doc_proc.extraction_status = ExtractionStatus.EXTRACTING.value
                doc_proc.extraction_attempted_at = datetime.now(UTC)
                doc_proc.extractor_name = CURRENT_EXTRACTOR_NAME
                doc_proc.extractor_version = CURRENT_EXTRACTOR_VERSION
                doc_proc.source_content_hash = file_rec.content_hash
                session.commit()

                try:
                    res = extractor.extract(abs_path)

                    # Check if extracted text hash is identical to previous extraction output
                    identical_text = (
                        doc_proc.extracted_text_hash is not None
                        and res.extracted_text_hash == doc_proc.extracted_text_hash
                        and doc_proc.chunking_status == ChunkingStatus.CHUNKED.value
                    )

                    # Execute DELETE-then-REINSERT for document segments
                    self.repository.delete_segments_and_chunks_for_doc(session, doc_proc.id)

                    for seg_data in res.segments:
                        seg = DocumentSegment(
                            document_processing_id=doc_proc.id,
                            segment_index=seg_data.segment_index,
                            segment_type=seg_data.segment_type,
                            page_number=seg_data.page_number,
                            text=seg_data.text,
                            char_count=seg_data.char_count,
                        )
                        session.add(seg)

                    doc_proc.extraction_status = ExtractionStatus.EXTRACTED.value
                    doc_proc.extracted_text_hash = res.extracted_text_hash
                    doc_proc.has_partial_errors = res.has_partial_errors
                    doc_proc.extraction_error_message = None

                    # A changed file must re-run chunking even if extraction succeeds and
                    # the hash was already updated. When the extracted text is unchanged,
                    # we can keep the prior completed chunking marker as-is.
                    if identical_text and doc_proc.chunking_status == ChunkingStatus.CHUNKED.value:
                        doc_proc.chunking_status = ChunkingStatus.CHUNKED.value
                    else:
                        doc_proc.chunking_status = ChunkingStatus.NOT_CHUNKED.value
                        doc_proc.chunking_error_message = None

                    session.commit()

                except Exception as err:
                    logger.warning("Extraction failed for %s: %s", file_rec.filename, err)
                    session.rollback()

                    doc_proc = session.get(DocumentProcessing, doc_proc_id)
                    if doc_proc:
                        doc_proc.extraction_status = ExtractionStatus.FAILED.value
                        doc_proc.extraction_error_message = sanitize_error_message(err)
                        doc_proc.extraction_error_count += 1
                        session.commit()
                    return

            # -----------------------------------------------------------------
            # Stage 2: Chunking (if needed)
            # -----------------------------------------------------------------
            needs_chk = self.needs_chunking(doc_proc, file_rec)

            if needs_chk:
                doc_proc.chunking_status = ChunkingStatus.CHUNKING.value
                doc_proc.chunking_attempted_at = datetime.now(UTC)
                doc_proc.chunker_name = CURRENT_CHUNKER_NAME
                doc_proc.chunker_version = CURRENT_CHUNKER_VERSION
                session.commit()

                try:
                    # Fetch stored segments
                    segments = doc_proc.segments
                    chunker = FixedChunker(chunk_size=1000, overlap=200)

                    # Execute DELETE-then-REINSERT for chunks
                    self.repository.delete_chunks_for_doc(session, doc_proc.id)

                    global_chunk_idx = 0
                    for seg in segments:
                        c_datas = chunker.chunk_segment(
                            segment_id=seg.id,
                            segment_text=seg.text,
                            starting_chunk_index=global_chunk_idx,
                        )
                        for cd in c_datas:
                            chunk = Chunk(
                                document_processing_id=doc_proc.id,
                                segment_id=seg.id,
                                chunk_index=cd.chunk_index,
                                text=cd.text,
                                char_start=cd.char_start,
                                char_end=cd.char_end,
                                char_count=cd.char_count,
                                content_hash=cd.content_hash,
                            )
                            session.add(chunk)
                            global_chunk_idx += 1

                    doc_proc.chunking_status = ChunkingStatus.CHUNKED.value
                    doc_proc.chunking_error_message = None
                    session.commit()

                except Exception as err:
                    logger.warning("Chunking failed for %s: %s", file_rec.filename, err)
                    session.rollback()

                    doc_proc = session.get(DocumentProcessing, doc_proc_id)
                    if doc_proc:
                        doc_proc.chunking_status = ChunkingStatus.FAILED.value
                        doc_proc.chunking_error_message = sanitize_error_message(err)
                        doc_proc.chunking_error_count += 1
                        session.commit()
