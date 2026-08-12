"""Create workspace_files, document_processing, and scan_jobs tables.

Revision ID: 20260812_0002
Revises: 20260808_0001
Create Date: 2026-08-12 00:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "20260812_0002"
down_revision = "20260808_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("relative_path", sa.String(length=2048), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("extension", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=64), server_default="unknown", nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("modified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("fs_status", sa.String(length=32), server_default="new", nullable=False),
        sa.Column(
            "last_scanned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
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
        sa.UniqueConstraint("workspace_id", "relative_path", name="uq_workspace_files_workspace_relpath"),
    )
    op.create_index("ix_workspace_files_workspace_id", "workspace_files", ["workspace_id"], unique=False)
    op.create_index(
        "ix_workspace_files_workspace_status",
        "workspace_files",
        ["workspace_id", "fs_status"],
        unique=False,
    )

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

    op.create_table(
        "scan_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="queued", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("files_discovered", sa.Integer(), server_default="0", nullable=False),
        sa.Column("files_processed", sa.Integer(), server_default="0", nullable=False),
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
    op.create_index("ix_scan_jobs_workspace_id", "scan_jobs", ["workspace_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_scan_jobs_workspace_id", table_name="scan_jobs")
    op.drop_table("scan_jobs")

    op.drop_index("ix_document_processing_workspace_file_id", table_name="document_processing")
    op.drop_table("document_processing")

    op.drop_index("ix_workspace_files_workspace_status", table_name="workspace_files")
    op.drop_index("ix_workspace_files_workspace_id", table_name="workspace_files")
    op.drop_table("workspace_files")
