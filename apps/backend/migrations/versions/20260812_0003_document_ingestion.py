"""Create document_processing overhaul, document_segments, chunks,
and document_processing_jobs tables.

Revision ID: 20260812_0003
Revises: 20260812_0002
Create Date: 2026-08-12 00:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "20260812_0003"
down_revision = "20260812_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing stub table if present and recreate full document_processing table
    op.drop_index("ix_document_processing_workspace_file_id", table_name="document_processing")
    op.drop_table("document_processing")

    op.create_table(
        "document_processing",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_file_id", sa.Integer(), nullable=False),
        sa.Column(
            "extraction_status",
            sa.String(length=32),
            server_default="unprocessed",
            nullable=False,
        ),
        sa.Column("extractor_name", sa.String(length=64), server_default="default", nullable=False),
        sa.Column(
            "extractor_version", sa.String(length=32), server_default="1.0.0", nullable=False
        ),
        sa.Column("source_content_hash", sa.String(length=64), nullable=True),
        sa.Column("extracted_text_hash", sa.String(length=64), nullable=True),
        sa.Column("extraction_error_message", sa.Text(), nullable=True),
        sa.Column("extraction_error_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("extraction_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("has_partial_errors", sa.Boolean(), server_default="0", nullable=False),
        sa.Column(
            "chunking_status",
            sa.String(length=32),
            server_default="not_chunked",
            nullable=False,
        ),
        sa.Column("chunker_name", sa.String(length=64), server_default="default", nullable=False),
        sa.Column("chunker_version", sa.String(length=32), server_default="1.0.0", nullable=False),
        sa.Column("chunking_error_message", sa.Text(), nullable=True),
        sa.Column("chunking_error_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("chunking_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["workspace_file_id"], ["workspace_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_file_id"),
    )
    op.create_index(
        "ix_document_processing_workspace_file_id",
        "document_processing",
        ["workspace_file_id"],
        unique=True,
    )

    op.create_table(
        "document_segments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_processing_id", sa.Integer(), nullable=False),
        sa.Column("segment_index", sa.Integer(), nullable=False),
        sa.Column("segment_type", sa.String(length=32), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_processing_id"], ["document_processing.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_segments_document_processing_id",
        "document_segments",
        ["document_processing_id"],
        unique=False,
    )
    op.create_index(
        "ix_document_segments_proc_segment_idx",
        "document_segments",
        ["document_processing_id", "segment_index"],
        unique=False,
    )

    op.create_table(
        "chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_processing_id", sa.Integer(), nullable=False),
        sa.Column("segment_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_processing_id"], ["document_processing.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["segment_id"], ["document_segments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chunks_document_processing_id", "chunks", ["document_processing_id"], unique=False
    )
    op.create_index("ix_chunks_segment_id", "chunks", ["segment_id"], unique=False)
    op.create_index(
        "ix_chunks_proc_chunk_idx",
        "chunks",
        ["document_processing_id", "chunk_index"],
        unique=False,
    )
    op.create_index(
        "ix_chunks_seg_chunk_idx", "chunks", ["segment_id", "chunk_index"], unique=False
    )

    op.create_table(
        "document_processing_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="queued", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_processing_jobs_workspace_id",
        "document_processing_jobs",
        ["workspace_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_processing_jobs_workspace_id", table_name="document_processing_jobs"
    )
    op.drop_table("document_processing_jobs")

    op.drop_index("ix_chunks_seg_chunk_idx", table_name="chunks")
    op.drop_index("ix_chunks_proc_chunk_idx", table_name="chunks")
    op.drop_index("ix_chunks_segment_id", table_name="chunks")
    op.drop_index("ix_chunks_document_processing_id", table_name="chunks")
    op.drop_table("chunks")

    op.drop_index("ix_document_segments_proc_segment_idx", table_name="document_segments")
    op.drop_index("ix_document_segments_document_processing_id", table_name="document_segments")
    op.drop_table("document_segments")

    op.drop_index("ix_document_processing_workspace_file_id", table_name="document_processing")
    op.drop_table("document_processing")

    op.create_table(
        "document_processing",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_file_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="unprocessed", nullable=False),
        sa.Column("last_processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["workspace_file_id"], ["workspace_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_file_id"),
    )
    op.create_index(
        "ix_document_processing_workspace_file_id",
        "document_processing",
        ["workspace_file_id"],
        unique=True,
    )
