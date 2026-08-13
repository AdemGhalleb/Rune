import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest
from docx import Document as DocxDocument
from pypdf import PdfWriter

from app.ai.chunking.fixed_chunker import FixedChunker
from app.ai.extraction.docx_extractor import DocxExtractor
from app.ai.extraction.pdf_extractor import PdfExtractor
from app.ai.extraction.text_extractor import TextExtractor
from app.db.models import (
    ChunkingStatus,
    DocumentProcessing,
    ExtractionStatus,
    Workspace,
    WorkspaceFile,
)
from app.db.workspace_file_repository import WorkspaceFileRepository
from app.workers.scan_runner import ScanManager


def test_text_markdown_extractors_and_chunker_offsets(tmp_path: Path) -> None:
    text_path = tmp_path / "notes.txt"
    text_path.write_text("Alpha beta gamma")

    md_path = tmp_path / "notes.md"
    md_path.write_text("# Heading\n\nMarkdown body")

    text_result = TextExtractor().extract(text_path)
    md_result = TextExtractor().extract(md_path)

    assert text_result.segments[0].segment_type == "plain_text"
    assert text_result.segments[0].text == "Alpha beta gamma"
    assert md_result.segments[0].segment_type == "plain_text"
    assert md_result.segments[0].text.replace("\r\n", "\n") == "# Heading\n\nMarkdown body"

    chunker = FixedChunker(chunk_size=5, overlap=2)
    chunks = chunker.chunk_segment(segment_id=7, segment_text="abcdefgh")

    assert [(chunk.char_start, chunk.char_end) for chunk in chunks] == [(0, 5), (3, 8)]
    assert all(chunk.segment_id == 7 for chunk in chunks)
    assert all(chunk.char_start >= 0 and chunk.char_end <= 8 for chunk in chunks)


def test_docx_and_pdf_extractors(tmp_path: Path) -> None:
    docx_path = tmp_path / "chapter.docx"
    doc = DocxDocument()
    doc.add_paragraph("Chapter body")
    doc.save(docx_path)

    pdf_path = tmp_path / "slides.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with pdf_path.open("wb") as handle:
        writer.write(handle)

    docx_result = DocxExtractor().extract(docx_path)
    pdf_result = PdfExtractor().extract(pdf_path)

    assert docx_result.segments[0].segment_type == "docx_paragraph_block"
    assert docx_result.segments[0].text == "Chapter body"
    assert pdf_result.segments[0].segment_type == "pdf_page"
    assert pdf_result.segments[0].page_number == 1
    assert len(pdf_result.segments) == 1


def test_startup_reconciliation_resets_orphaned_rows(session_factory, tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()

    with session_factory() as session:
        workspace = Workspace(root_path=str(root), name="Reconcile Test")
        session.add(workspace)
        session.flush()

        file_rec = WorkspaceFile(
            workspace_id=workspace.id,
            relative_path="chapter.txt",
            filename="chapter.txt",
            extension=".txt",
            category="note",
            size_bytes=16,
            modified_at=datetime.now(UTC),
            content_hash="abc123",
            fs_status="unchanged",
        )
        session.add(file_rec)
        session.flush()

        doc_proc = DocumentProcessing(
            workspace_file_id=file_rec.id,
            extraction_status=ExtractionStatus.EXTRACTING.value,
            chunking_status=ChunkingStatus.CHUNKING.value,
            extraction_error_message="stale extraction error",
            chunking_error_message="stale chunking error",
        )
        session.add(doc_proc)
        session.commit()

        repo = WorkspaceFileRepository()
        reset_count = repo.reconcile_orphaned_doc_processing_states(session, workspace.id)
        assert reset_count == 2

        refreshed = session.get(DocumentProcessing, doc_proc.id)
        assert refreshed is not None
        assert refreshed.extraction_status == ExtractionStatus.UNPROCESSED.value
        assert refreshed.chunking_status == ChunkingStatus.NOT_CHUNKED.value
        assert refreshed.extraction_error_message is None
        assert refreshed.chunking_error_message is None


@pytest.mark.asyncio
async def test_scan_handoff_auto_enqueues_changed_text_file(
    session_factory, tmp_path: Path
) -> None:
    root = tmp_path / "scan_workspace"
    root.mkdir()

    target = root / "draft.txt"
    target.write_text("alpha beta gamma")

    with session_factory() as session:
        workspace = Workspace(root_path=str(root), name="Auto Enqueue")
        session.add(workspace)
        session.commit()
        workspace_id = workspace.id

    runner = ScanManager(session_factory)
    repo = WorkspaceFileRepository()

    first_job = await runner.start_scan(workspace_id)
    assert first_job.status == "running"

    active_first = runner._active_scans.get(workspace_id)
    if active_first:
        await active_first.task

    with session_factory() as session:
        file_rec = repo.get_by_relative_path(session, workspace_id, "draft.txt")
        assert file_rec is not None
        file_id = file_rec.id

    for _ in range(50):
        with session_factory() as session:
            doc_proc = repo.get_document_processing_by_file_id(session, file_id)
            if (
                doc_proc
                and doc_proc.extraction_status == ExtractionStatus.EXTRACTED.value
                and doc_proc.chunking_status == ChunkingStatus.CHUNKED.value
            ):
                break
        await asyncio.sleep(0.1)

    with session_factory() as session:
        doc_proc = repo.get_document_processing_by_file_id(session, file_id)
        assert doc_proc is not None
        first_segment_ids = [segment.id for segment in doc_proc.segments]
        first_chunk_ids = [chunk.id for chunk in doc_proc.chunks]
        assert first_segment_ids
        assert first_chunk_ids

    target.write_text("zulu yankee xray whiskey victor")

    second_job = await runner.start_scan(workspace_id)
    assert second_job.id != first_job.id

    active_second = runner._active_scans.get(workspace_id)
    if active_second:
        await active_second.task

    with session_factory() as session:
        updated_file = repo.get_by_relative_path(session, workspace_id, "draft.txt")
        assert updated_file is not None
        updated_hash = updated_file.content_hash

    for _ in range(100):
        with session_factory() as session:
            doc_proc = repo.get_document_processing_by_file_id(session, file_id)
            if (
                doc_proc
                and doc_proc.source_content_hash == updated_hash
                and doc_proc.extraction_status == ExtractionStatus.EXTRACTED.value
                and doc_proc.chunking_status == ChunkingStatus.CHUNKED.value
                and doc_proc.segments
                and doc_proc.segments[0].text == "zulu yankee xray whiskey victor"
            ):
                break
        await asyncio.sleep(0.1)

    with session_factory() as session:
        doc_proc = repo.get_document_processing_by_file_id(session, file_id)
        assert doc_proc is not None
        assert doc_proc.source_content_hash == updated_hash
        assert len(doc_proc.segments) == 1
        assert len(doc_proc.chunks) == 1
        assert doc_proc.segments[0].text == "zulu yankee xray whiskey victor"
