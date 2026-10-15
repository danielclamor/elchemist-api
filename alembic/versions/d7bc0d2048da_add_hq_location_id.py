"""add hq_location_id

Revision ID: d7bc0d2048da
Revises: da0a8414bd60
Create Date: 2026-10-15 15:48:36.045237

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd7bc0d2048da'
down_revision: Union[str, Sequence[str], None] = 'da0a8414bd60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  op.add_column("production_orders", sa.Column("hq_location_id", sa.Uuid(), nullable=True))
  op.create_index("ix_production_orders_hq_location_id", "production_orders", ["hq_location_id"])
  op.create_foreign_key(
    "fk_production_orders_hq_location_id",
    "production_orders", "locations", ["hq_location_id"], ["id"],
  )
  op.execute(
    "UPDATE production_orders "
    "SET hq_location_id = (SELECT id FROM locations WHERE is_hq) "
    "WHERE hq_location_id IS NULL"
  )

def downgrade() -> None:
  op.drop_constraint("fk_production_orders_hq_location_id", "production_orders", type_="foreignkey")
  op.drop_index("ix_production_orders_hq_location_id", table_name="production_orders")
  op.drop_column("production_orders", "hq_location_id")
