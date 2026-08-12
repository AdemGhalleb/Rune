"""In-process background scan runner with single-flight execution and live progress updates."""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from app.db.models import ScanJob, ScanJobStatus, Workspace
from app.db.workspace_file_repository import WorkspaceFileRepository
from app.workspace.change_detector import IncrementalChangeDetector, ScanCancelledError
from app.workspace.scanner import WorkspaceScanner

logger = logging.getLogger(__name__)


@dataclass
class ActiveScan:
    job_id: int
    cancel_event: asyncio.Event
    task: asyncio.Task


class ScanManager:
    """Manages active background scan jobs for Rune workspaces."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory
        self.repository = WorkspaceFileRepository()
        self._active_scans: dict[int, ActiveScan] = {}
        self._lock = asyncio.Lock()

    async def start_scan(self, workspace_id: int) -> ScanJob:
        """Start a background scan job for a workspace, enforcing single-flight execution."""
        async with self._lock:
            # Check if scan is already active for this workspace
            active = self._active_scans.get(workspace_id)
            if active and not active.task.done():
                logger.info("Scan job already running for workspace %s (job %s)", workspace_id, active.job_id)
                with self.session_factory() as session:
                    existing_job = session.get(ScanJob, active.job_id)
                    if existing_job:
                        return existing_job

            # Create scan job record in DB
            with self.session_factory() as session:
                workspace = session.get(Workspace, workspace_id)
                if not workspace:
                    raise ValueError(f"Workspace {workspace_id} not found")
                root_path = Path(workspace.root_path)

                job = self.repository.create_scan_job(session, workspace_id)
                job_id = job.id

            cancel_event = asyncio.Event()
            task = asyncio.create_task(
                self._run_scan_task(job_id, workspace_id, root_path, cancel_event)
            )
            self._active_scans[workspace_id] = ActiveScan(
                job_id=job_id, cancel_event=cancel_event, task=task
            )

            return job

    async def cancel_scan(self, workspace_id: int) -> bool:
        """Cancel a running scan job for a workspace."""
        async with self._lock:
            active = self._active_scans.get(workspace_id)
            if not active or active.task.done():
                return False

            active.cancel_event.set()
            logger.info("Cancellation requested for workspace %s (job %s)", workspace_id, active.job_id)
            return True

    def is_scan_running(self, workspace_id: int) -> bool:
        active = self._active_scans.get(workspace_id)
        return active is not None and not active.task.done()

    async def _run_scan_task(
        self, job_id: int, workspace_id: int, root_path: Path, cancel_event: asyncio.Event
    ) -> None:
        """Execute filesystem discovery and change detection in thread pool off the main event loop."""
        try:
            logger.info("Starting scan task for workspace %s (job %s)", workspace_id, job_id)

            def is_cancelled() -> bool:
                return cancel_event.is_set()

            def perform_scan_and_sync() -> None:
                scanner = WorkspaceScanner(root_path)
                discovered = scanner.scan()

                if is_cancelled():
                    raise ScanCancelledError("Scan cancelled during discovery")

                # Update files_discovered count
                with self.session_factory() as session:
                    self.repository.update_scan_job_progress(
                        session, job_id, files_discovered=len(discovered)
                    )

                detector = IncrementalChangeDetector(repository=self.repository)

                last_progress_update = [0]

                def progress_cb(processed: int) -> None:
                    # Update live progress every 20 items to reduce DB write noise
                    if processed - last_progress_update[0] >= 20 or processed == len(discovered):
                        last_progress_update[0] = processed
                        with self.session_factory() as session:
                            self.repository.update_scan_job_progress(
                                session, job_id, files_processed=processed
                            )

                with self.session_factory() as session:
                    detector.process_scan_results(
                        session,
                        workspace_id,
                        root_path,
                        discovered,
                        is_cancelled=is_cancelled,
                        progress_callback=progress_cb,
                    )

            await asyncio.to_thread(perform_scan_and_sync)

            with self.session_factory() as session:
                self.repository.update_scan_job_progress(
                    session, job_id, status=ScanJobStatus.COMPLETED.value
                )
            logger.info("Completed scan task for workspace %s (job %s)", workspace_id, job_id)

        except ScanCancelledError:
            logger.info("Scan task cancelled for workspace %s (job %s)", workspace_id, job_id)
            with self.session_factory() as session:
                self.repository.update_scan_job_progress(
                    session, job_id, status=ScanJobStatus.CANCELLED.value
                )
        except Exception as err:
            logger.exception("Scan task failed for workspace %s (job %s): %s", workspace_id, job_id, err)
            with self.session_factory() as session:
                self.repository.update_scan_job_progress(
                    session, job_id, status=ScanJobStatus.FAILED.value, error=str(err)
                )
        finally:
            async with self._lock:
                active = self._active_scans.get(workspace_id)
                if active and active.job_id == job_id:
                    del self._active_scans[workspace_id]
