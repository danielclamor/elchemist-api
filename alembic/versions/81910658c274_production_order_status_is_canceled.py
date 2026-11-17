"""production order status: FULFILLED/IN_PROGRESS/PENDING/MIXED/PUMPED + is_canceled

Revision ID: 81910658c274
Revises: 335ed41089ee
Create Date: 2026-11-17 16:55:00.000000

Status values become FULFILLED, IN_PROGRESS, PENDING, MIXED, PUMPED.
  - DELIVERED  -> FULFILLED
  - CANCELLED  -> is_canceled = true. The stage it was cancelled at is not
                  stored, so the status falls back to FULFILLED when a
                  fulfilled_quantity was recorded, otherwise PENDING.
Hand-written: the data has to be converted while the enum type is swapped.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '81910658c274'
down_revision: Union[str, Sequence[str], None] = '335ed41089ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _swap_enum(values: tuple[str, ...], using: str) -> None:
    op.execute("ALTER TYPE productionorderstatus RENAME TO productionorderstatus_old")
    labels = ", ".join(f"'{v}'" for v in values)
    op.execute(f"CREATE TYPE productionorderstatus AS ENUM ({labels})")
    op.execute(
        "ALTER TABLE production_orders ALTER COLUMN status "
        f"TYPE productionorderstatus USING ({using})::productionorderstatus"
    )
    op.execute("DROP TYPE productionorderstatus_old")


def upgrade() -> None:
    op.add_column(
        'production_orders',
        sa.Column('is_canceled', sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.execute("UPDATE production_orders SET is_canceled = true WHERE status::text = 'CANCELLED'")
    _swap_enum(
        ('FULFILLED', 'IN_PROGRESS', 'PENDING', 'MIXED', 'PUMPED'),
        """CASE status::text
             WHEN 'DELIVERED' THEN 'FULFILLED'
             WHEN 'CANCELLED' THEN (CASE WHEN fulfilled_quantity IS NOT NULL
                                         THEN 'FULFILLED' ELSE 'PENDING' END)
             ELSE status::text
           END""",
    )


def downgrade() -> None:
    # MIXED / PUMPED did not exist before: they fall back to IN_PROGRESS
    # (is_canceled orders become CANCELLED again; DELIVERED cannot be told
    # apart from FULFILLED, so FULFILLED stays FULFILLED)
    _swap_enum(
        ('CANCELLED', 'DELIVERED', 'FULFILLED', 'IN_PROGRESS', 'PENDING'),
        """CASE WHEN is_canceled THEN 'CANCELLED'
                WHEN status::text IN ('MIXED', 'PUMPED') THEN 'IN_PROGRESS'
                ELSE status::text
           END""",
    )
    op.drop_column('production_orders', 'is_canceled')
