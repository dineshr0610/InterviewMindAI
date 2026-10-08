"""Add assessment state, profile, coding submissions, and evaluation metadata.

Revision ID: 004_assessment_extensions
Revises: 003_add_resume_and_safety_limit
"""

from alembic import op
import sqlalchemy as sa


revision = "004_assessment_extensions"
down_revision = "003_add_resume_and_safety_limit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("interviews", sa.Column("phase", sa.String(length=50), nullable=False, server_default="technical"))
    op.add_column("interviews", sa.Column("candidate_profile", sa.JSON(), nullable=True))
    op.add_column("interviews", sa.Column("role_snapshot", sa.JSON(), nullable=True))
    op.add_column("interviews", sa.Column("resume_match", sa.JSON(), nullable=True))
    op.add_column("interviews", sa.Column("assessment_state", sa.JSON(), nullable=True))
    op.add_column("interviews", sa.Column("final_assessment", sa.JSON(), nullable=True))
    op.add_column("interviews", sa.Column("coding_result", sa.JSON(), nullable=True))
    op.add_column("interviews", sa.Column("last_answer_fingerprint", sa.String(length=64), nullable=True))

    op.add_column("interview_messages", sa.Column("topic", sa.String(length=255), nullable=True))
    op.add_column("interview_messages", sa.Column("question_difficulty", sa.String(length=50), nullable=True))
    op.add_column("interview_messages", sa.Column("question_type", sa.String(length=80), nullable=True))
    op.add_column("interview_messages", sa.Column("technical_concept", sa.String(length=255), nullable=True))
    op.add_column("interview_messages", sa.Column("technical_evaluation", sa.JSON(), nullable=True))
    op.add_column("interview_messages", sa.Column("communication_evaluation", sa.JSON(), nullable=True))
    op.add_column("interview_messages", sa.Column("answer_fingerprint", sa.String(length=64), nullable=True))

    op.execute("DROP TABLE IF EXISTS code_submissions CASCADE")
    op.create_table(
        "code_submissions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("interview_id", sa.UUID(), nullable=False),
        sa.Column("problem_id", sa.String(length=100), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_code_submissions_id"), "code_submissions", ["id"], unique=False)
    op.create_index(op.f("ix_code_submissions_interview_id"), "code_submissions", ["interview_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_code_submissions_interview_id"), table_name="code_submissions")
    op.drop_index(op.f("ix_code_submissions_id"), table_name="code_submissions")
    op.drop_table("code_submissions")

    op.drop_column("interview_messages", "answer_fingerprint")
    op.drop_column("interview_messages", "communication_evaluation")
    op.drop_column("interview_messages", "technical_evaluation")
    op.drop_column("interview_messages", "technical_concept")
    op.drop_column("interview_messages", "question_type")
    op.drop_column("interview_messages", "question_difficulty")
    op.drop_column("interview_messages", "topic")

    op.drop_column("interviews", "last_answer_fingerprint")
    op.drop_column("interviews", "coding_result")
    op.drop_column("interviews", "final_assessment")
    op.drop_column("interviews", "assessment_state")
    op.drop_column("interviews", "resume_match")
    op.drop_column("interviews", "role_snapshot")
    op.drop_column("interviews", "candidate_profile")
    op.drop_column("interviews", "phase")
