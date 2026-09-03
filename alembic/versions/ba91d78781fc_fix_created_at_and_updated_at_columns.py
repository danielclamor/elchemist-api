"""fix created_at and updated_at columns

Revision ID: ba91d78781fc
Revises: 59bd53057ab9
Create Date: 2026-09-01 16:39:31.608671

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ba91d78781fc'
down_revision: Union[str, Sequence[str], None] = '59bd53057ab9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TIMESTAMP_COLUMNS = [
    ('eliquids', 'created_at'),
    ('eliquids', 'updated_at'),
    ('formulas', 'created_at'),
    ('formulas', 'updated_at'),
    ('nic_profiles', 'created_at'),
    ('nic_profiles', 'updated_at'),
    ('production_orders', 'created_at'),
    ('production_orders', 'updated_at'),
    ('production_order_activity_logs', 'triggered_at'),
]
 
 
def upgrade() -> None:
    """Upgrade schema."""
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            server_default=sa.text('now()'),
        )
 
 
def downgrade() -> None:
    """Downgrade schema."""
    for table, column in TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            column,
            server_default=None,
        )