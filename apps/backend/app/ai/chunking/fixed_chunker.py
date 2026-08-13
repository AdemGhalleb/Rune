"""Fixed-size segment-local text chunker."""

import hashlib
from dataclasses import dataclass

CURRENT_CHUNKER_NAME = "rune_fixed_chunker"
CURRENT_CHUNKER_VERSION = "1.0.0"


@dataclass
class ChunkData:
    chunk_index: int
    segment_id: int
    text: str
    char_start: int
    char_end: int
    char_count: int
    content_hash: str


class FixedChunker:
    """Fixed-size sliding-window chunker operating strictly within individual segments."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be non-negative and strictly less than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_segment(
        self, segment_id: int, segment_text: str, starting_chunk_index: int = 0
    ) -> list[ChunkData]:
        """Chunk a single segment's text into segment-local chunks.

        Chunks never cross segment boundaries. char_start and char_end are segment-local offsets.
        """
        if not segment_text:
            return []

        text_len = len(segment_text)
        chunks: list[ChunkData] = []
        step = self.chunk_size - self.overlap
        current_index = starting_chunk_index

        start = 0
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk_str = segment_text[start:end]

            chash = hashlib.sha256(chunk_str.encode("utf-8")).hexdigest()

            chunks.append(
                ChunkData(
                    chunk_index=current_index,
                    segment_id=segment_id,
                    text=chunk_str,
                    char_start=start,
                    char_end=end,
                    char_count=len(chunk_str),
                    content_hash=chash,
                )
            )

            current_index += 1
            if end >= text_len:
                break
            start += step

        return chunks
