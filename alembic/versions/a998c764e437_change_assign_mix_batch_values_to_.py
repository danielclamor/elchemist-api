"""change ASSIGN_MIX_BATCH values to mixNumber

Revision ID: a998c764e437
Revises: 0aab2746f9fe
Create Date: 2026-11-11 11:51:21.043353

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a998c764e437'
down_revision: Union[str, Sequence[str], None] = '0aab2746f9fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
      UPDATE production_order_activity_logs
      SET new_value = mix_batches.mix_number
      FROM production_orders
      JOIN mix_batches ON production_orders.mix_batch_id = mix_batches.id
      WHERE production_order_activity_logs.production_order_id = production_orders.id
        AND production_order_activity_logs.type = 'ASSIGN_MIX_BATCH'
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE production_order_activity_logs
        SET new_value = 'MIX'
        WHERE action = 'ASSIGN_MIX_BATCH'
    """)
