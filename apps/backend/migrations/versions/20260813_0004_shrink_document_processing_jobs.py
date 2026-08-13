"""Shrink document_processing_jobs to marker-only state.

Revision ID: 20260813_0004
Revises: 20260812_0003
Create Date: 2026-08-13 00:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "20260813_0004"
down_revision = "20260812_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("document_processing_jobs") as batch:
        batch.drop_column("error")
        batch.drop_column("created_at")
        batch.drop_column("updated_at")


def downgrade() -> None:
    with op.batch_alter_table("document_processing_jobs") as batch:
        batch.add_column(sa.Column("error", sa.Text(), nullable=True))
        batch.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            )
        )
        batch.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            )
        )