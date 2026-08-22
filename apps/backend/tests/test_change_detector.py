"""Tests for incremental change detector algorithm."""

from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import FsStatus, Workspace
from app.db.workspace_file_repository import WorkspaceFileRepository
from app.workspace.change_detector import IncrementalChangeDetector, ScanCancelledError
from app.workspace.scanner import WorkspaceScanner


def test_change_detector_lifecycle(db_session: Session, tmp_path: Path):
    root = tmp_path / "academic_workspace"
    root.mkdir()

    # Create workspace in DB
    ws = Workspace(root_path=str(root), name="Test Workspace")
    db_session.add(ws)
    db_session.commit()
    db_session.refresh(ws)

    # Step A: Initial scan (empty workspace)
    repo = WorkspaceFileRepository()
    detector = IncrementalChangeDetector(repository=repo)
    scanner = WorkspaceScanner(root)

    results = scanner.scan()
    detector.process_scan_results(db_session, ws.id, root, results)

    files = repo.get_by_workspace(db_session, ws.id)
    assert len(files) == 0

    # Step B: Add 2 new files
    f1 = root / "lecture1.pdf"
    f1.write_bytes(b"%PDF-1.4 initial content")

    f2 = root / "notes.md"
    f2.write_text("# Chapter 1 Notes")

    results = scanner.scan()
    detector.process_scan_results(db_session, ws.id, root, results)

    files = repo.get_by_workspace(db_session, ws.id)
    assert len(files) == 2
    assert all(f.fs_status == FsStatus.NEW.value for f in files)
    assert all(f.doc_processing is not None for f in files)

    # Step C: Second scan without modifications -> UNCHANGED
    results = scanner.scan()
    detector.process_scan_results(db_session, ws.id, root, results)

    files = repo.get_by_workspace(db_session, ws.id)
    assert len(files) == 2
    assert all(f.fs_status == FsStatus.UNCHANGED.value for f in files)

    # Step D: Modify notes.md
    f2.write_text("# Chapter 1 Notes (Updated)")
    results = scanner.scan()
    detector.process_scan_results(db_session, ws.id, root, results)

    rec_notes = repo.get_by_relative_path(db_session, ws.id, "notes.md")
    assert rec_notes is not None
    assert rec_notes.fs_status == FsStatus.MODIFIED.value

    # Step E: Rename notes.md -> notes_v2.md
    f2.rename(root / "notes_v2.md")
    results = scanner.scan()
    detector.process_scan_results(db_session, ws.id, root, results)

    # Rename should match existing record ID
    rec_renamed = repo.get_by_relative_path(db_session, ws.id, "notes_v2.md")
    assert rec_renamed is not None
    assert rec_renamed.id == rec_notes.id
    assert rec_renamed.fs_status == FsStatus.UNCHANGED.value

    old_notes = repo.get_by_relative_path(db_session, ws.id, "notes.md")
    assert old_notes is None  # Updated relative path in place

    # Step F: Delete lecture1.pdf
    f1.unlink()
    results = scanner.scan()
    detector.process_scan_results(db_session, ws.id, root, results)

    rec_f1 = repo.get_by_relative_path(db_session, ws.id, "lecture1.pdf")
    assert rec_f1 is not None
    assert rec_f1.fs_status == FsStatus.DELETED.value


def test_change_detector_cancellation(db_session: Session, tmp_path: Path):
    root = tmp_path / "workspace"
    root.mkdir()

    ws = Workspace(root_path=str(root), name="Cancel Workspace")
    db_session.add(ws)
    db_session.commit()

    (root / "doc1.txt").write_text("content 1")
    (root / "doc2.txt").write_text("content 2")

    scanner = WorkspaceScanner(root)
    results = scanner.scan()

    detector = IncrementalChangeDetector()
    cancelled = False

    def is_cancelled():
        return cancelled

    cancelled = True
    try:
        detector.process_scan_results(db_session, ws.id, root, results, is_cancelled=is_cancelled)
        assert False, "Should have raised ScanCancelledError"
    except ScanCancelledError:
        pass
