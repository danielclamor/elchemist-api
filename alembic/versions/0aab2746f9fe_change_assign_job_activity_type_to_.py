"""change ASSIGN_JOB activity type to ASSIGN_MIX_BATCH

Revision ID: 0aab2746f9fe
Revises: ec78abcac001
Create Date: 2026-11-11 11:48:10.210964

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0aab2746f9fe'
down_revision: Union[str, Sequence[str], None] = 'ec78abcac001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
      UPDATE production_order_activity_logs SET type = 'ASSIGN_MIX_BATCH' WHERE type = 'ASSIGN_JOB'
    """)


def downgrade() -> None:
    op.execute("""
      UPDATE production_order_activity_logs SET type = 'ASSIGN_JOB' WHERE type = 'ASSIGN_MIX_BATCH'
    """)
