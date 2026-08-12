"""Ignore policy for workspace scanning."""

import fnmatch

# Directory names to immediately prune during directory traversal
IGNORED_DIRECTORIES: set[str] = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    "target",
    ".cache",
    ".idea",
    ".vscode",
    ".obsidian",
    ".ds_store",
    "$recycle.bin",
    "system volume information",
}

# File name fnmatch patterns for temporary/editor/system files
IGNORED_FILE_PATTERNS: tuple[str, ...] = (
    "~$*.docx",
    "~$*.xlsx",
    "*.tmp",
    "*.swp",
    "thumbs.db",
    ".ds_store",
    "*.lock",
    "*.pyc",
    "*.pyo",
)


def should_ignore_directory(dir_name: str) -> bool:
    """Return True if the directory name should be pruned immediately."""
    name_lower = dir_name.strip().lower()
    return name_lower in IGNORED_DIRECTORIES or name_lower.startswith(".git")


def should_ignore_file(filename: str) -> bool:
    """Return True if the file matches common temporary/editor/system patterns."""
    name_lower = filename.strip().lower()
    for pattern in IGNORED_FILE_PATTERNS:
        if fnmatch.fnmatch(name_lower, pattern):
            return True
    return False
