"""remove assign to repat activity log

Revision ID: 5b0b670308f7
Revises: 59a6e115f18c
Create Date: 2026-11-11 11:24:02.197106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b0b670308f7'
down_revision: Union[str, Sequence[str], None] = '59a6e115f18c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('''
        CREATE TABLE _backup_repat_logs AS
        SELECT * FROM production_order_activity_logs
        WHERE old_value = 'REPAT' OR new_value = 'REPAT'
    ''')
    op.execute('''
      DELETE FROM production_order_activity_logs
      WHERE old_value = 'REPAT' OR new_value = 'REPAT'
    ''')


def downgrade() -> None:
    op.execute('''
        INSERT INTO production_order_activity_logs
        SELECT * FROM _backup_repat_logs
    ''')
    op.execute('DROP TABLE _backup_repat_logs')
