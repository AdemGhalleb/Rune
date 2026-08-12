"""File extension category classification."""

_CATEGORY_MAPPING: dict[str, str] = {
    # Documents
    ".pdf": "document",
    ".docx": "document",
    ".doc": "document",
    ".epub": "document",
    ".odt": "document",
    ".rtf": "document",
    ".txt": "document",
    # Notes
    ".md": "note",
    ".markdown": "note",
    ".rst": "note",
    ".org": "note",
    # Presentations
    ".pptx": "presentation",
    ".ppt": "presentation",
    ".key": "presentation",
    # Spreadsheets
    ".xlsx": "spreadsheet",
    ".xls": "spreadsheet",
    ".csv": "spreadsheet",
    ".tsv": "spreadsheet",
    # Code & Data
    ".py": "code",
    ".ts": "code",
    ".tsx": "code",
    ".js": "code",
    ".jsx": "code",
    ".html": "code",
    ".css": "code",
    ".json": "code",
    ".yaml": "code",
    ".yml": "code",
    ".toml": "code",
    ".c": "code",
    ".cpp": "code",
    ".h": "code",
    ".rs": "code",
    ".java": "code",
    ".go": "code",
    ".sql": "code",
    ".sh": "code",
    ".ps1": "code",
    # Images
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".svg": "image",
    ".webp": "image",
    # Archives
    ".zip": "archive",
    ".tar": "archive",
    ".gz": "archive",
    ".7z": "archive",
    ".rar": "archive",
}


def categorize_file(extension: str) -> str:
    """Determine category string from file extension (lowercase with dot)."""
    ext_clean = extension.strip().lower()
    if not ext_clean.startswith(".") and ext_clean:
        ext_clean = f".{ext_clean}"
    return _CATEGORY_MAPPING.get(ext_clean, "unknown")
