"""Create the workspace table.

Revision ID: 20260808_0001
Revises:
Create Date: 2026-08-08 00:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "20260808_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("root_path", sa.String(length=2048), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("root_path"),
    )
    op.create_index("ix_workspaces_root_path", "workspaces", ["root_path"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_workspaces_root_path", table_name="workspaces")
    op.drop_table("workspaces")
