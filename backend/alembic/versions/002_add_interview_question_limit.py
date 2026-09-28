"""Add the persisted Week 1 interview question limit.

Revision ID: 002_add_interview_question_limit
Revises: 001_initial_schema
"""

from alembic import op
import sqlalchemy as sa


revision = "002_add_interview_question_limit"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "interviews",
        sa.Column("max_questions", sa.Integer(), nullable=False, server_default="5"),
    )
    op.alter_column("interviews", "max_questions", server_default=None)


def downgrade() -> None:
    op.drop_column("interviews", "max_questions")
