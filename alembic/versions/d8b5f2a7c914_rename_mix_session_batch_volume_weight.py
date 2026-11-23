"""rename mix_sessions total_volume_ml/total_weight_g to batch_volume_ml/batch_weight_g

Revision ID: d8b5f2a7c914
Revises: a169eae111c3
Create Date: 2026-11-23 15:05:00.000000

Column renames only; no data changes. (Autogenerate would drop and add the
columns, losing the data.)
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd8b5f2a7c914'
down_revision: Union[str, Sequence[str], None] = 'a169eae111c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('mix_sessions', 'total_volume_ml', new_column_name='batch_volume_ml')
    op.alter_column('mix_sessions', 'total_weight_g', new_column_name='batch_weight_g')


def downgrade() -> None:
    op.alter_column('mix_sessions', 'batch_weight_g', new_column_name='total_weight_g')
    op.alter_column('mix_sessions', 'batch_volume_ml', new_column_name='total_volume_ml')
