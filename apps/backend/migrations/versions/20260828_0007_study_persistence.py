"""Add persistent study sessions, flashcards, quizzes, attempts, and citations.

Revision ID: 20260828_0007
Revises: 20260822_0006
"""

import sqlalchemy as sa
from alembic import op

revision = "20260828_0007"
down_revision = "20260822_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. study_sessions
    op.create_table(
        "study_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("session_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=True),
        sa.Column("workspace_file_id", sa.Integer(), nullable=True),
        sa.Column("content_json", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["workspace_file_id"], ["workspace_files.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_study_sessions_workspace_id", "study_sessions", ["workspace_id"], unique=False
    )
    op.create_index(
        "ix_study_sessions_workspace_file_id",
        "study_sessions",
        ["workspace_file_id"],
        unique=False,
    )
    op.create_index(
        "ix_study_sessions_workspace_type",
        "study_sessions",
        ["workspace_id", "session_type"],
        unique=False,
    )

    # 2. study_flashcards
    op.create_table(
        "study_flashcards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("card_index", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("review_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("state", sa.String(length=32), server_default="new", nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["study_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_study_flashcards_session_id", "study_flashcards", ["session_id"], unique=False
    )
    op.create_index(
        "ix_study_flashcards_session_idx",
        "study_flashcards",
        ["session_id", "card_index"],
        unique=False,
    )

    # 3. study_quiz_questions
    op.create_table(
        "study_quiz_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("question_index", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("options_json", sa.Text(), nullable=False),
        sa.Column("correct_index", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["study_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_study_quiz_questions_session_id", "study_quiz_questions", ["session_id"], unique=False
    )
    op.create_index(
        "ix_study_quiz_questions_session_idx",
        "study_quiz_questions",
        ["session_id", "question_index"],
        unique=False,
    )

    # 4. study_quiz_attempts
    op.create_table(
        "study_quiz_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("answers_json", sa.Text(), nullable=False),
        sa.Column(
            "completed_at",
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
        sa.ForeignKeyConstraint(["session_id"], ["study_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_study_quiz_attempts_session_id", "study_quiz_attempts", ["session_id"], unique=False
    )
    op.create_index(
        "ix_study_quiz_attempts_session_created",
        "study_quiz_attempts",
        ["session_id", "created_at"],
        unique=False,
    )

    # 5. study_session_citations
    op.create_table(
        "study_session_citations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column("workspace_file_id", sa.Integer(), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("rank", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["study_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chunk_id"], ["chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_file_id"], ["workspace_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id", "chunk_id", name="uq_study_session_citations_chunk"
        ),
    )
    op.create_index(
        "ix_study_session_citations_session_id",
        "study_session_citations",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_study_session_citations_chunk_id",
        "study_session_citations",
        ["chunk_id"],
        unique=False,
    )
    op.create_index(
        "ix_study_session_citations_workspace_file_id",
        "study_session_citations",
        ["workspace_file_id"],
        unique=False,
    )

    # 6. study_flashcard_citations
    op.create_table(
        "study_flashcard_citations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("flashcard_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column("workspace_file_id", sa.Integer(), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["flashcard_id"], ["study_flashcards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chunk_id"], ["chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_file_id"], ["workspace_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_study_flashcard_citations_flashcard_id",
        "study_flashcard_citations",
        ["flashcard_id"],
        unique=False,
    )
    op.create_index(
        "ix_study_flashcard_citations_chunk_id",
        "study_flashcard_citations",
        ["chunk_id"],
        unique=False,
    )
    op.create_index(
        "ix_study_flashcard_citations_workspace_file_id",
        "study_flashcard_citations",
        ["workspace_file_id"],
        unique=False,
    )

    # 7. study_quiz_question_citations
    op.create_table(
        "study_quiz_question_citations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quiz_question_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column("workspace_file_id", sa.Integer(), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["quiz_question_id"], ["study_quiz_questions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["chunk_id"], ["chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_file_id"], ["workspace_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_study_quiz_question_citations_quiz_question_id",
        "study_quiz_question_citations",
        ["quiz_question_id"],
        unique=False,
    )
    op.create_index(
        "ix_study_quiz_question_citations_chunk_id",
        "study_quiz_question_citations",
        ["chunk_id"],
        unique=False,
    )
    op.create_index(
        "ix_study_quiz_question_citations_workspace_file_id",
        "study_quiz_question_citations",
        ["workspace_file_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("study_quiz_question_citations")
    op.drop_table("study_flashcard_citations")
    op.drop_table("study_session_citations")
    op.drop_table("study_quiz_attempts")
    op.drop_table("study_quiz_questions")
    op.drop_table("study_flashcards")
    op.drop_table("study_sessions")
