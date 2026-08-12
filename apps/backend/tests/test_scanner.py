"""Tests for workspace scanner and ignore policy."""

from pathlib import Path

from app.workspace.ignore_policy import should_ignore_directory, should_ignore_file
from app.workspace.scanner import WorkspaceScanner


def test_ignore_policy():
    assert should_ignore_directory(".git")
    assert should_ignore_directory("node_modules")
    assert should_ignore_directory(".venv")
    assert not should_ignore_directory("documents")

    assert should_ignore_file("~$lecture.docx")
    assert should_ignore_file("notes.tmp")
    assert should_ignore_file(".DS_Store")
    assert not should_ignore_file("lecture.pdf")


def test_scanner_discovers_files(tmp_path: Path):
    root = tmp_path / "workspace"
    root.mkdir()

    # Create nested structure
    sub = root / "course1"
    sub.mkdir()
    (sub / "notes.md").write_text("Hello notes")
    (root / "paper.pdf").write_bytes(b"%PDF-1.4 test")

    # Create ignored folder with files inside
    git_dir = root / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("git config")

    # Create ignored temp file
    (root / "~$temp.docx").write_text("temp")

    scanner = WorkspaceScanner(root)
    results = scanner.scan()

    rel_paths = {f.relative_path for f in results}
    assert "course1/notes.md" in rel_paths
    assert "paper.pdf" in rel_paths
    assert "~$temp.docx" in rel_paths

    ignored_paths = {f.relative_path for f in results if f.is_ignored}
    assert "~$temp.docx" in ignored_paths

    # .git directory files should be pruned completely
    assert not any(f.relative_path.startswith(".git") for f in results)


def test_scanner_symlink_safety(tmp_path: Path):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "file1.txt").write_text("inside")

    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret")

    # Create symlink pointing outside
    try:
        (root / "outside_link").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        # Symlinks may require privileges on Windows; skip if unsupported
        return

    scanner = WorkspaceScanner(root)
    results = scanner.scan()

    # Secret file outside workspace should NOT be indexed
    assert not any("secret.txt" in f.relative_path for f in results)
