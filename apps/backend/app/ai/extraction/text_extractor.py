"""Plain text and Markdown document extractor with encoding detection."""

import logging
from pathlib import Path

import chardet

from app.ai.extraction.base import (
    BaseExtractor,
    ExtractionResult,
    SegmentData,
    compute_text_hash,
)

logger = logging.getLogger(__name__)


class TextExtractor(BaseExtractor):
    """Text & Markdown document extractor."""

    def extract(self, file_path: Path) -> ExtractionResult:
        raw_bytes = file_path.read_bytes()
        text = self._decode_bytes(raw_bytes, file_path)

        clean_text = text.strip()
        segments: list[SegmentData] = [
            SegmentData(
                segment_index=0,
                segment_type="plain_text",
                text=clean_text,
                char_count=len(clean_text),
                page_number=None,
            )
        ]

        logger.info("Extracted text file %s (%d chars)", file_path.name, len(clean_text))

        text_hash = compute_text_hash(clean_text)
        return ExtractionResult(
            segments=segments,
            extracted_text_hash=text_hash,
            has_partial_errors=False,
        )

    def _decode_bytes(self, raw_bytes: bytes, file_path: Path) -> str:
        """Attempt robust decoding using UTF-8, chardet, or latin-1."""
        if not raw_bytes:
            return ""

        # Attempt UTF-8 / UTF-8 with BOM first
        try:
            return raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            pass

        # Attempt chardet
        detected = chardet.detect(raw_bytes)
        encoding = detected.get("encoding")
        if encoding:
            try:
                return raw_bytes.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                logger.debug(
                    "Failed decoding file %s with detected encoding %s",
                    file_path.name,
                    encoding,
                )

        # Fallback to latin-1 (guaranteed to decode any byte string)
        return raw_bytes.decode("latin-1")
