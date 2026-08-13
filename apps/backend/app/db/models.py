from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class FsStatus(StrEnum):
    NEW = "new"
    UNCHANGED = "unchanged"
    MODIFIED = "modified"
    DELETED = "deleted"
    IGNORED = "ignored"
    ERROR = "error"


class ExtractionStatus(StrEnum):
    UNPROCESSED = "unprocessed"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    FAILED = "failed"


class ChunkingStatus(StrEnum):
    NOT_CHUNKED = "not_chunked"
    CHUNKING = "chunking"
    CHUNKED = "chunked"
    FAILED = "failed"


class SegmentType(StrEnum):
    PDF_PAGE = "pdf_page"
    DOCX_PARAGRAPH_BLOCK = "docx_paragraph_block"
    PLAIN_TEXT = "plain_text"


class ScanJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DocProcessingJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Workspace(Base):
    """The single academic workspace selected by the student."""

    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    root_path: Mapped[str] = mapped_column(String(2048), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    files: Mapped[list["WorkspaceFile"]] = relationship(
        "WorkspaceFile", back_populates="workspace", cascade="all, delete-orphan"
    )
    scan_jobs: Mapped[list["ScanJob"]] = relationship(
        "ScanJob", back_populates="workspace", cascade="all, delete-orphan"
    )
    doc_processing_jobs: Mapped[list["DocumentProcessingJob"]] = relationship(
        "DocumentProcessingJob", back_populates="workspace", cascade="all, delete-orphan"
    )


class WorkspaceFile(Base):
    """File metadata persistent index within a workspace."""

    __tablename__ = "workspace_files"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "relative_path", name="uq_workspace_files_workspace_relpath"
        ),
        Index("ix_workspace_files_workspace_status", "workspace_id", "fs_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relative_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    extension: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    modified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fs_status: Mapped[str] = mapped_column(String(32), nullable=False, default=FsStatus.NEW.value)
    last_scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="files")
    doc_processing: Mapped["DocumentProcessing | None"] = relationship(
        "DocumentProcessing",
        back_populates="workspace_file",
        uselist=False,
        cascade="all, delete-orphan",
    )


class DocumentProcessing(Base):
    """Document processing status and tracking (Phase 2 boundary)."""

    __tablename__ = "document_processing"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_file_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspace_files.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    extraction_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ExtractionStatus.UNPROCESSED.value
    )
    extractor_name: Mapped[str] = mapped_column(String(64), nullable=False, default="default")
    extractor_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    source_content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extracted_text_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extraction_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extraction_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    has_partial_errors: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    chunking_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ChunkingStatus.NOT_CHUNKED.value
    )
    chunker_name: Mapped[str] = mapped_column(String(64), nullable=False, default="default")
    chunker_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    chunking_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunking_error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunking_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    workspace_file: Mapped[WorkspaceFile] = relationship(
        "WorkspaceFile", back_populates="doc_processing"
    )
    segments: Mapped[list["DocumentSegment"]] = relationship(
        "DocumentSegment",
        back_populates="document_processing",
        cascade="all, delete-orphan",
        order_by="DocumentSegment.segment_index",
    )
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="document_processing",
        cascade="all, delete-orphan",
        order_by="Chunk.chunk_index",
    )


class DocumentSegment(Base):
    """Format-agnostic extracted document segment (e.g. PDF page or DOCX block)."""

    __tablename__ = "document_segments"
    __table_args__ = (
        Index("ix_document_segments_proc_segment_idx", "document_processing_id", "segment_index"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_processing_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("document_processing.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    segment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    document_processing: Mapped[DocumentProcessing] = relationship(
        "DocumentProcessing", back_populates="segments"
    )
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk", back_populates="segment", cascade="all, delete-orphan"
    )


class Chunk(Base):
    """Chunk of text extracted within a single document segment."""

    __tablename__ = "chunks"
    __table_args__ = (
        Index("ix_chunks_proc_chunk_idx", "document_processing_id", "chunk_index"),
        Index("ix_chunks_seg_chunk_idx", "segment_id", "chunk_index"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_processing_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("document_processing.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("document_segments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    document_processing: Mapped[DocumentProcessing] = relationship(
        "DocumentProcessing", back_populates="chunks"
    )
    segment: Mapped[DocumentSegment] = relationship("DocumentSegment", back_populates="chunks")


class DocumentProcessingJob(Base):
    """Marker row for document ingestion runs (progress computed live from document_processing)."""

    __tablename__ = "document_processing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=DocProcessingJobStatus.QUEUED.value
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="doc_processing_jobs")


class ScanJob(Base):
    """Persistent workspace scan execution tracking."""

    __tablename__ = "scan_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ScanJobStatus.QUEUED.value
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    files_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="scan_jobs")

