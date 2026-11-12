"""new order and session number counters

Revision ID: b4e8d1f6a203
Revises: 6f9a1b323318
Create Date: 2026-11-12 13:45:00.000000

Production orders: one running counter, so numbers are 1000, 1001, 1002, ...
  (existing orders keep their old numbers; the counter also skips past any plain
  number already in use, e.g. a hand-made order 1005)
Mix sessions: one counter row per day, for MIX-{yyyy}{mm}{dd}{count} numbers.
  (existing sessions keep their old numbers, e.g. MIX-01)

The old counter tables are replaced. Hand-written: the changes are data-aware.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4e8d1f6a203'
down_revision: Union[str, Sequence[str], None] = '6f9a1b323318'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # production orders: a single counter row, starting so that the first number is 1000
    op.create_table('production_order_counter',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('last_number', sa.Integer(), nullable=False),
        sa.CheckConstraint('id = 1', name='ck_production_order_counter_single_row'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.execute("""
        INSERT INTO production_order_counter (id, last_number)
        SELECT 1, GREATEST(999, COALESCE(MAX(order_number::bigint), 0))
        FROM production_orders
        WHERE order_number ~ '^[0-9]{1,9}$'
    """)

    # mix sessions: one row per day
    op.create_table('mix_session_counters',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('last_number', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('date'),
    )

    # the old counters are no longer used
    op.drop_table('production_order_counters')
    op.drop_table('mix_session_counter')


def downgrade() -> None:
    """Downgrade schema."""
    # old single-number session counter, restarted from the number of existing sessions
    op.create_table('mix_session_counter',
        sa.Column('last_number', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('last_number'),
    )
    op.execute("INSERT INTO mix_session_counter (last_number) SELECT COUNT(*) FROM mix_sessions")

    # old daily order counter, rebuilt from the old-format order numbers (yyyymmdd + 5 digits)
    op.create_table('production_order_counters',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('last_number', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('date'),
    )
    op.execute("""
        INSERT INTO production_order_counters (date, last_number)
        SELECT to_date(substr(order_number, 1, 8), 'YYYYMMDD'), MAX(substr(order_number, 9)::int)
        FROM production_orders
        WHERE order_number ~ '^20[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[0-9]{5}$'
        GROUP BY 1
    """)

    op.drop_table('mix_session_counters')
    op.drop_table('production_order_counter')
