"""Tests for ScanManager background scan job runner."""

import asyncio
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.db.models import ScanJobStatus, Workspace
from app.db.workspace_file_repository import WorkspaceFileRepository
from app.workers.scan_runner import ScanManager


@pytest.mark.asyncio
async def test_scan_runner_execution(session_factory, tmp_path: Path):
    root = tmp_path / "scan_workspace"
    root.mkdir()

    (root / "doc1.pdf").write_bytes(b"%PDF content 1")
    (root / "doc2.md").write_text("# Chapter 1")

    # Create workspace record
    with session_factory() as session:
        ws = Workspace(root_path=str(root), name="Scan Runner Test")
        session.add(ws)
        session.commit()
        ws_id = ws.id

    runner = ScanManager(session_factory)
    job = await runner.start_scan(ws_id)
    assert job.status == ScanJobStatus.RUNNING.value

    # Wait for background task completion
    active = runner._active_scans.get(ws_id)
    if active:
        await active.task

    repo = WorkspaceFileRepository()
    with session_factory() as session:
        latest = repo.get_latest_scan_job(session, ws_id)
        assert latest is not None
        assert latest.status == ScanJobStatus.COMPLETED.value
        assert latest.files_discovered == 2
        assert latest.files_processed == 2

        files = repo.get_by_workspace(session, ws_id)
        assert len(files) == 2


@pytest.mark.asyncio
async def test_scan_runner_single_flight(session_factory, tmp_path: Path):
    root = tmp_path / "single_flight_workspace"
    root.mkdir()

    with session_factory() as session:
        ws = Workspace(root_path=str(root), name="Single Flight")
        session.add(ws)
        session.commit()
        ws_id = ws.id

    runner = ScanManager(session_factory)

    job1 = await runner.start_scan(ws_id)
    job2 = await runner.start_scan(ws_id)

    # Duplicate call must return same active job ID
    assert job1.id == job2.id

    active = runner._active_scans.get(ws_id)
    if active:
        await active.task


@pytest.mark.asyncio
async def test_scan_runner_cancellation(session_factory, tmp_path: Path):
    root = tmp_path / "cancel_workspace"
    root.mkdir()

    # Create many files to allow cancellation window
    for i in range(100):
        (root / f"file_{i}.txt").write_text(f"content {i}")

    with session_factory() as session:
        ws = Workspace(root_path=str(root), name="Cancel Test")
        session.add(ws)
        session.commit()
        ws_id = ws.id

    runner = ScanManager(session_factory)
    job = await runner.start_scan(ws_id)

    # Cancel immediately
    cancelled = await runner.cancel_scan(ws_id)
    assert cancelled is True

    active = runner._active_scans.get(ws_id)
    if active:
        try:
            await active.task
        except Exception:
            pass

    repo = WorkspaceFileRepository()
    with session_factory() as session:
        latest = repo.get_latest_scan_job(session, ws_id)
        assert latest is not None
        assert latest.status in (ScanJobStatus.CANCELLED.value, ScanJobStatus.COMPLETED.value)

