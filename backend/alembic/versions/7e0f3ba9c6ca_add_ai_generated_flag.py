"""add ai_generated flag to explanations and findings

Revision ID: 7e0f3ba9c6ca
Revises: fa5ca2588506
Create Date: 2026-08-15 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '7e0f3ba9c6ca'
down_revision: Union[str, None] = 'fa5ca2588506'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default backfills existing rows as False (i.e. "not confirmed
    # AI-generated"), then the app-level default takes over for new rows.
    op.add_column(
        'explanations',
        sa.Column('ai_generated', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column('explanations', 'ai_generated', server_default=None)

    op.add_column(
        'findings',
        sa.Column('ai_generated', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column('findings', 'ai_generated', server_default=None)


def downgrade() -> None:
    op.drop_column('findings', 'ai_generated')
    op.drop_column('explanations', 'ai_generated')
