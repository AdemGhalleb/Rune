"""Page-by-page PDF extractor implementation using pypdf."""

import logging
from pathlib import Path

from pypdf import PdfReader

from app.ai.extraction.base import (
    BaseExtractor,
    ExtractionResult,
    SegmentData,
    compute_text_hash,
    sanitize_error_message,
)

logger = logging.getLogger(__name__)


class PdfExtractor(BaseExtractor):
    """Page-by-page PDF extractor."""

    def extract(self, file_path: Path) -> ExtractionResult:
        reader = PdfReader(str(file_path))
        segments: list[SegmentData] = []
        has_partial_errors = False
        all_text_parts: list[str] = []

        total_pages = len(reader.pages)
        logger.info("Extracting PDF %s (%d pages)", file_path.name, total_pages)

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            try:
                text = page.extract_text() or ""
                clean_text = text.strip()
                segments.append(
                    SegmentData(
                        segment_index=idx,
                        segment_type="pdf_page",
                        text=clean_text,
                        char_count=len(clean_text),
                        page_number=page_num,
                    )
                )
                all_text_parts.append(clean_text)
            except Exception as err:
                logger.warning(
                    "Error extracting page %d of PDF %s: %s",
                    page_num,
                    file_path.name,
                    sanitize_error_message(err),
                )
                has_partial_errors = True
                segments.append(
                    SegmentData(
                        segment_index=idx,
                        segment_type="pdf_page",
                        text="",
                        char_count=0,
                        page_number=page_num,
                    )
                )

        combined_text = "\n\n".join(all_text_parts)
        text_hash = compute_text_hash(combined_text)

        return ExtractionResult(
            segments=segments,
            extracted_text_hash=text_hash,
            has_partial_errors=has_partial_errors,
        )
