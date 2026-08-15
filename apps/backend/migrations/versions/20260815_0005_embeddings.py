"""Alembic migration: chunk_embeddings table and chunk_vectors virtual table.

Revision ID: 20260815_0005
Revises: 20260813_0004
Create Date: 2026-08-15 00:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "20260815_0005"
down_revision = "20260813_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chunk_embeddings",
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("embedding_model_id", sa.String(length=128), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="not_embedded",
            nullable=False,
        ),
        sa.Column("content_hash_at_embedding", sa.String(length=64), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
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
        sa.ForeignKeyConstraint(["chunk_id"], ["chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chunk_id"),
        sa.UniqueConstraint("chunk_id"),
    )
    op.create_index(
        "ix_chunk_embeddings_workspace_id",
        "chunk_embeddings",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_chunk_embeddings_workspace_status",
        "chunk_embeddings",
        ["workspace_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_chunk_embeddings_model_id",
        "chunk_embeddings",
        ["embedding_model_id"],
        unique=False,
    )

def downgrade() -> None:
    op.drop_index("ix_chunk_embeddings_model_id", table_name="chunk_embeddings")
    op.drop_index("ix_chunk_embeddings_workspace_status", table_name="chunk_embeddings")
    op.drop_index("ix_chunk_embeddings_workspace_id", table_name="chunk_embeddings")
    op.drop_table("chunk_embeddings")
