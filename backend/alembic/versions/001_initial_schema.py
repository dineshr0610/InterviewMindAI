"""Initial schema creation for interviews and interview_messages

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-07-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create interview status enum type if using PostgreSQL
    interview_status_enum = postgresql.ENUM('ACTIVE', 'COMPLETED', 'TERMINATED', name='interview_status', create_type=False)
    
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        interview_status_enum.create(bind, checkfirst=True)

    # Create interviews table
    op.create_table(
        'interviews',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('candidate_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=255), nullable=False),
        sa.Column('topic', sa.String(length=255), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=False, server_default='Easy'),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'COMPLETED', 'TERMINATED', name='interview_status', create_type=False), nullable=False, server_default='ACTIVE'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interviews_id'), 'interviews', ['id'], unique=False)
    op.create_index(op.f('ix_interviews_candidate_name'), 'interviews', ['candidate_name'], unique=False)
    op.create_index(op.f('ix_interviews_status'), 'interviews', ['status'], unique=False)

    # Create interview_messages table
    op.create_table(
        'interview_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('interview_id', sa.UUID(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('strengths', sa.Text(), nullable=True),
        sa.Column('improvements', sa.Text(), nullable=True),
        sa.Column('next_question', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_messages_id'), 'interview_messages', ['id'], unique=False)
    op.create_index(op.f('ix_interview_messages_interview_id'), 'interview_messages', ['interview_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_interview_messages_interview_id'), table_name='interview_messages')
    op.drop_index(op.f('ix_interview_messages_id'), table_name='interview_messages')
    op.drop_table('interview_messages')

    op.drop_index(op.f('ix_interviews_status'), table_name='interviews')
    op.drop_index(op.f('ix_interviews_candidate_name'), table_name='interviews')
    op.drop_index(op.f('ix_interviews_id'), table_name='interviews')
    op.drop_table('interviews')

    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        interview_status_enum = postgresql.ENUM('ACTIVE', 'COMPLETED', 'TERMINATED', name='interview_status')
        interview_status_enum.drop(bind, checkfirst=True)
