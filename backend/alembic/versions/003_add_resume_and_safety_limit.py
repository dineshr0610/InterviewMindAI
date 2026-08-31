"""Add resume_text to interviews and raise the internal safety limit.

Revision ID: 003_add_resume_and_safety_limit
Revises: 002_add_interview_question_limit
"""

from alembic import op
import sqlalchemy as sa


revision = "003_add_resume_and_safety_limit"
down_revision = "002_add_interview_question_limit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "interviews",
        sa.Column("resume_text", sa.Text(), nullable=True),
    )
    op.alter_column(
        "interviews",
        "max_questions",
        server_default="50",
    )


def downgrade() -> None:
    op.alter_column(
        "interviews",
        "max_questions",
        server_default="5",
    )
    op.drop_column("interviews", "resume_text")
