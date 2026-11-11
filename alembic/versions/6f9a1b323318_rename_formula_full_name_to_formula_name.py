"""rename formula full name to formula name

Revision ID: 6f9a1b323318
Revises: a9d4e6b2c071
Create Date: 2026-11-11 15:43:18.650139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f9a1b323318'
down_revision: Union[str, Sequence[str], None] = 'a9d4e6b2c071'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('mix_sessions', 'formula_full_name_snapshot', new_column_name='formula_name_snapshot')

def downgrade() -> None:
    op.alter_column('mix_sessions', 'formula_name_snapshot', new_column_name='formula_full_name_snapshot')
