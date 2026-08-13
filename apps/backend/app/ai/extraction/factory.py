"""Factory mapping file extensions to extractor instances."""

from pathlib import Path

from app.ai.extraction.base import BaseExtractor
from app.ai.extraction.docx_extractor import DocxExtractor
from app.ai.extraction.pdf_extractor import PdfExtractor
from app.ai.extraction.text_extractor import TextExtractor

CURRENT_EXTRACTOR_NAME = "rune_standard_extractor"
CURRENT_EXTRACTOR_VERSION = "1.0.0"


def get_extractor_for_file(file_path: Path) -> BaseExtractor | None:
    """Return extractor instance for supported document extensions, or None if unsupported."""
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return PdfExtractor()
    elif ext == ".docx":
        return DocxExtractor()
    elif ext in (".txt", ".md"):
        return TextExtractor()
    return None
