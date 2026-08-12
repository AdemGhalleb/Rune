"""Incremental change detection engine for workspace synchronization."""

import logging
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import DocProcessingStatus, DocumentProcessing, FsStatus, WorkspaceFile
from app.db.workspace_file_repository import WorkspaceFileRepository
from app.workspace.hasher import compute_sha256
from app.workspace.scanner import DiscoveredFile

logger = logging.getLogger(__name__)


class ScanCancelledError(Exception):
    """Raised when a running scan job is explicitly cancelled."""


class IncrementalChangeDetector:
    """Compares discovered filesystem entries with persistent database state to detect changes."""

    def __init__(
        self,
        repository: WorkspaceFileRepository | None = None,
        batch_size: int = 200,
    ) -> None:
        self.repository = repository or WorkspaceFileRepository()
        self.batch_size = batch_size

    def process_scan_results(
        self,
        session: Session,
        workspace_id: int,
        root_path: Path,
        discovered_files: list[DiscoveredFile],
        is_cancelled: Callable[[], bool] | None = None,
        progress_callback: Callable[[int], None] | None = None,
    ) -> dict[str, int]:
        """Perform incremental change detection and persist results to SQLite."""
        existing_records = self.repository.get_by_workspace(session, workspace_id)
        existing_by_relpath: dict[str, WorkspaceFile] = {f.relative_path: f for f in existing_records}

        new_candidates: list[tuple[DiscoveredFile, str | None]] = []
        matched_existing_ids: set[int] = set()

        processed_count = 0
        now_utc = datetime.now(timezone.utc)

        # Step 1 & 2: Evaluate discovered files against existing DB records
        for disc in discovered_files:
            if is_cancelled and is_cancelled():
                raise ScanCancelledError("Scan job was cancelled by user")

            rel_path = disc.relative_path
            abs_path = root_path / rel_path

            if disc.has_error:
                rec = existing_by_relpath.get(rel_path)
                if rec:
                    rec.fs_status = FsStatus.ERROR.value
                    rec.last_scanned_at = now_utc
                    matched_existing_ids.add(rec.id)
                else:
                    new_rec = WorkspaceFile(
                        workspace_id=workspace_id,
                        relative_path=rel_path,
                        filename=disc.filename,
                        extension=disc.extension,
                        category=disc.category,
                        size_bytes=0,
                        modified_at=disc.modified_at,
                        content_hash=None,
                        fs_status=FsStatus.ERROR.value,
                        last_scanned_at=now_utc,
                    )
                    session.add(new_rec)
                processed_count += 1
                if progress_callback:
                    progress_callback(processed_count)
                continue

            if disc.is_ignored:
                rec = existing_by_relpath.get(rel_path)
                if rec:
                    rec.fs_status = FsStatus.IGNORED.value
                    rec.last_scanned_at = now_utc
                    matched_existing_ids.add(rec.id)
                else:
                    new_rec = WorkspaceFile(
                        workspace_id=workspace_id,
                        relative_path=rel_path,
                        filename=disc.filename,
                        extension=disc.extension,
                        category=disc.category,
                        size_bytes=disc.size_bytes,
                        modified_at=disc.modified_at,
                        content_hash=None,
                        fs_status=FsStatus.IGNORED.value,
                        last_scanned_at=now_utc,
                    )
                    session.add(new_rec)
                processed_count += 1
                if progress_callback:
                    progress_callback(processed_count)
                continue

            if rel_path in existing_by_relpath:
                rec = existing_by_relpath[rel_path]
                matched_existing_ids.add(rec.id)

                # Cheap check: compare size and mtime (within 0.001s timestamp resolution)
                size_matches = disc.size_bytes == rec.size_bytes

                disc_ts = disc.modified_at.replace(tzinfo=timezone.utc).timestamp() if disc.modified_at.tzinfo is None else disc.modified_at.timestamp()
                rec_ts = rec.modified_at.replace(tzinfo=timezone.utc).timestamp() if rec.modified_at.tzinfo is None else rec.modified_at.timestamp()
                mtime_matches = abs(disc_ts - rec_ts) < 0.001

                if size_matches and mtime_matches and rec.fs_status != FsStatus.DELETED.value:
                    rec.fs_status = FsStatus.UNCHANGED.value
                    rec.last_scanned_at = now_utc
                else:
                    # Possible modification: compute content hash
                    try:
                        computed_hash = compute_sha256(abs_path)
                    except Exception as err:
                        logger.warning("Could not hash file %s: %s", abs_path, err)
                        rec.fs_status = FsStatus.ERROR.value
                        rec.last_scanned_at = now_utc
                        processed_count += 1
                        if progress_callback:
                            progress_callback(processed_count)
                        continue

                    if computed_hash == rec.content_hash:
                        rec.fs_status = FsStatus.UNCHANGED.value
                    else:
                        rec.fs_status = FsStatus.MODIFIED.value

                    rec.size_bytes = disc.size_bytes
                    rec.modified_at = disc.modified_at
                    rec.content_hash = computed_hash
                    rec.last_scanned_at = now_utc
            else:
                # Candidate for NEW or RENAME
                new_candidates.append((disc, None))

            processed_count += 1
            if progress_callback:
                progress_callback(processed_count)

            if processed_count % self.batch_size == 0:
                session.commit()

        # Step 3: Identify deleted candidates (existing non-deleted files not found in scan)
        deleted_candidates = [
            rec for rel_path, rec in existing_by_relpath.items()
            if rec.id not in matched_existing_ids and rec.fs_status != FsStatus.DELETED.value
        ]

        # Step 4: Rename Detection (within single scan)
        # Compute hashes for new candidates if needed
        computed_new_candidates: list[tuple[DiscoveredFile, str]] = []
        for disc, _ in new_candidates:
            if is_cancelled and is_cancelled():
                raise ScanCancelledError("Scan job was cancelled by user")
            abs_path = root_path / disc.relative_path
            try:
                chash = compute_sha256(abs_path)
                computed_new_candidates.append((disc, chash))
            except Exception as err:
                logger.warning("Failed hashing new file %s: %s", abs_path, err)
                new_rec = WorkspaceFile(
                    workspace_id=workspace_id,
                    relative_path=disc.relative_path,
                    filename=disc.filename,
                    extension=disc.extension,
                    category=disc.category,
                    size_bytes=disc.size_bytes,
                    modified_at=disc.modified_at,
                    content_hash=None,
                    fs_status=FsStatus.ERROR.value,
                    last_scanned_at=now_utc,
                )
                session.add(new_rec)

        matched_renames: set[int] = set()
        matched_new_relpaths: set[str] = set()

        for disc, new_hash in computed_new_candidates:
            if disc.size_bytes == 0:
                continue  # Skip rename matching for 0-byte files
            for del_rec in deleted_candidates:
                if del_rec.id in matched_renames:
                    continue
                if del_rec.size_bytes == disc.size_bytes and del_rec.content_hash == new_hash:
                    # Match found! Treat as rename
                    del_rec.relative_path = disc.relative_path
                    del_rec.filename = disc.filename
                    del_rec.extension = disc.extension
                    del_rec.category = disc.category
                    del_rec.modified_at = disc.modified_at
                    del_rec.fs_status = FsStatus.UNCHANGED.value
                    del_rec.last_scanned_at = now_utc
                    matched_renames.add(del_rec.id)
                    matched_new_relpaths.add(disc.relative_path)
                    logger.info(
                        "Detected rename in workspace %s: %s -> %s",
                        workspace_id,
                        del_rec.relative_path,
                        disc.relative_path,
                    )
                    break

        # Step 5: Process remaining NEW candidates
        for disc, new_hash in computed_new_candidates:
            if disc.relative_path in matched_new_relpaths:
                continue
            new_file = WorkspaceFile(
                workspace_id=workspace_id,
                relative_path=disc.relative_path,
                filename=disc.filename,
                extension=disc.extension,
                category=disc.category,
                size_bytes=disc.size_bytes,
                modified_at=disc.modified_at,
                content_hash=new_hash,
                fs_status=FsStatus.NEW.value,
                last_scanned_at=now_utc,
            )
            session.add(new_file)
            session.flush()  # Generate surrogate ID

            doc_proc = DocumentProcessing(
                workspace_file_id=new_file.id,
                status=DocProcessingStatus.UNPROCESSED.value,
            )
            session.add(doc_proc)

        # Step 6: Process remaining DELETED candidates
        for del_rec in deleted_candidates:
            if del_rec.id in matched_renames:
                continue
            del_rec.fs_status = FsStatus.DELETED.value
            del_rec.last_scanned_at = now_utc

        session.commit()

        # Calculate final change counts
        overview = self.repository.get_overview_stats(session, workspace_id)
        return overview["files_by_status"]
