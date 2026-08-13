"""Base definitions for document extraction."""

import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SegmentData:
    segment_index: int
    segment_type: str
    text: str
    char_count: int
    page_number: int | None = None


@dataclass
class ExtractionResult:
    segments: list[SegmentData]
    extracted_text_hash: str
    has_partial_errors: bool = False
    error_message: str | None = None


def sanitize_error_message(err: Exception | str, max_len: int = 420) -> str:
    """Sanitize and truncate error messages before persisting them."""
    msg = str(err).strip().splitlines()[0].strip()
    msg = re.sub(r"\s+", " ", msg)
    msg = re.sub(r"([`'\"])(.{24,}?)\1", "[redacted]", msg)

    # Keep structural error descriptions, but trim long content-like tails aggressively.
    if len(msg.split()) > 40:
        msg = " ".join(msg.split()[:40])

    if len(msg) > max_len:
        msg = msg[: max_len - 3].rstrip() + "..."

    return msg


def compute_text_hash(text: str) -> str:
    """Compute SHA-256 hash of extracted text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_workspace_path(file_path: Path, workspace_root: Path) -> None:
    """Ensure file path stays within workspace root and is safe to open."""
    resolved_root = workspace_root.resolve()
    resolved_file = file_path.resolve()

    try:
        resolved_file.relative_to(resolved_root)
    except ValueError as err:
        raise ValueError(
            f"Security boundary violation: File {file_path.name} resides outside workspace root."
        ) from err


class BaseExtractor(ABC):
    """Abstract base class for format-specific document extractors."""

    @abstractmethod
    def extract(self, file_path: Path) -> ExtractionResult:
        """Extract segments from document file."""
        pass
