"""mix_batch_counter auto seeder

Revision ID: 33fe85e28db5
Revises: 38926dcb67a1
Create Date: 2026-10-27 11:08:53.457694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33fe85e28db5'
down_revision: Union[str, Sequence[str], None] = '38926dcb67a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  op.execute("""
    INSERT INTO mix_batch_counter (last_number)
    SELECT (SELECT COUNT(*) FROM mix_batches)
    WHERE NOT EXISTS (SELECT 1 FROM mix_batch_counter)
  """)

def downgrade() -> None:
  """Downgrade schema."""
  pass
