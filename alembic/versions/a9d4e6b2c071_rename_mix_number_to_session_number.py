"""rename mix_number to session_number

Revision ID: a9d4e6b2c071
Revises: f7a3c1d9e5b2
Create Date: 2026-11-11 14:30:00.000000

Hand-written: autogenerate can't detect a column rename (it would drop the column
and its data). Renames mix_sessions.mix_number to session_number together with its
unique index. Stored values (e.g. "MIX-01") are unchanged.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a9d4e6b2c071'
down_revision: Union[str, Sequence[str], None] = 'f7a3c1d9e5b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('mix_sessions', 'mix_number', new_column_name='session_number')
    op.execute('ALTER INDEX ix_mix_sessions_mix_number RENAME TO ix_mix_sessions_session_number')


def downgrade() -> None:
    op.execute('ALTER INDEX ix_mix_sessions_session_number RENAME TO ix_mix_sessions_mix_number')
    op.alter_column('mix_sessions', 'session_number', new_column_name='mix_number')
