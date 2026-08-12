"""Recursive workspace scanner with boundary safety and cheap metadata collection."""

import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.workspace.category import categorize_file
from app.workspace.ignore_policy import should_ignore_directory, should_ignore_file

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DiscoveredFile:
    relative_path: str
    filename: str
    extension: str
    category: str
    size_bytes: int
    modified_at: datetime
    is_ignored: bool = False
    has_error: bool = False
    error_detail: str | None = None


class WorkspaceScanner:
    """Discovers files inside a workspace folder safely and collects cheap stat metadata."""

    def __init__(self, root_path: str | Path) -> None:
        self.root_path = Path(root_path).expanduser().resolve()

    def is_inside_workspace(self, target_path: Path) -> bool:
        """Verify that resolved target_path resides inside root_path."""
        try:
            resolved_target = target_path.resolve()
            resolved_root = self.root_path
            return resolved_target == resolved_root or resolved_root in resolved_target.parents
        except Exception:
            return False

    def scan(self) -> list[DiscoveredFile]:
        """Scan workspace recursively, returning cheap metadata for discovered files."""
        if not self.root_path.exists() or not self.root_path.is_dir():
            logger.warning(
                "Workspace root path does not exist or is not a directory: %s", self.root_path
            )
            return []

        discovered: list[DiscoveredFile] = []
        self._scan_directory(self.root_path, discovered)
        return discovered

    def _scan_directory(self, current_dir: Path, out_files: list[DiscoveredFile]) -> None:
        """Recursively scan directory entries with boundary checks and error isolation."""
        try:
            entries = list(os.scandir(current_dir))
        except Exception as err:
            logger.warning("Failed to list directory %s: %s", current_dir, err)
            return

        for entry in entries:
            try:
                entry_path = Path(entry.path)
                name = entry.name

                # Check symlink / reparse point safety
                if entry.is_symlink():
                    if not self.is_inside_workspace(entry_path):
                        logger.debug("Skipping symlink outside workspace: %s", entry_path)
                        continue

                if entry.is_dir(follow_symlinks=False):
                    if should_ignore_directory(name):
                        logger.debug("Pruning ignored directory: %s", name)
                        continue
                    self._scan_directory(entry_path, out_files)

                elif entry.is_file(follow_symlinks=False):
                    rel_path = self._to_relative_path(entry_path)
                    if rel_path is None:
                        continue

                    ignored = should_ignore_file(name)

                    try:
                        stat_res = entry.stat(follow_symlinks=False)
                        size_bytes = stat_res.st_size
                        mtime_dt = datetime.fromtimestamp(stat_res.st_mtime, tz=UTC)
                        ext = entry_path.suffix.lower()
                        cat = categorize_file(ext)

                        out_files.append(
                            DiscoveredFile(
                                relative_path=rel_path,
                                filename=name,
                                extension=ext,
                                category=cat,
                                size_bytes=size_bytes,
                                modified_at=mtime_dt,
                                is_ignored=ignored,
                                has_error=False,
                            )
                        )
                    except Exception as stat_err:
                        # Broad exception handling for unreadable/cloud sync placeholder files
                        logger.warning(
                            "Error reading metadata for file %s: %s", entry_path, stat_err
                        )
                        ext = entry_path.suffix.lower()
                        out_files.append(
                            DiscoveredFile(
                                relative_path=rel_path,
                                filename=name,
                                extension=ext,
                                category=categorize_file(ext),
                                size_bytes=0,
                                modified_at=datetime.now(UTC),
                                is_ignored=ignored,
                                has_error=True,
                                error_detail=str(stat_err),
                            )
                        )
            except Exception as entry_err:
                logger.warning(
                    "Unexpected error inspecting directory entry in %s: %s",
                    current_dir,
                    entry_err,
                )
                continue

    def _to_relative_path(self, target_path: Path) -> str | None:
        """Calculate relative path with forward slashes for cross-platform consistency."""
        try:
            rel = target_path.relative_to(self.root_path)
            return rel.as_posix()
        except ValueError:
            return None
