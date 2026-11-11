"""add assign_mix_batch activity type

Revision ID: ec78abcac001
Revises: 92269d050f62
Create Date: 2026-11-11 11:36:18.439453

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec78abcac001'
down_revision: Union[str, Sequence[str], None] = '92269d050f62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE productionorderactivitytype ADD VALUE IF NOT EXISTS 'ASSIGN_MIX_BATCH'")

def downgrade() -> None:
    op.execute("ALTER TYPE productionorderactivitytype RENAME TO productionorderactivitytypeold")
    op.execute("CREATE TYPE productionorderactivitytype AS ENUM('CREATED', 'ADJUST_QUANTITY', 'CHANGE_STATUS', 'SWITCH_PRIORITY', 'TOGGLE_ARCHIVED', 'ASSIGN_JOB')")
    
    op.execute("DELETE FROM production_order_activity_logs WHERE type = 'ASSIGN_MIX_BATCH'")
    
    op.execute(
        "ALTER TABLE production_order_activity_logs ALTER COLUMN type TYPE productionorderactivitytype "
        "USING type::text::productionorderactivitytype"
    )
    op.execute("DROP TYPE productionorderactivitytypeold")
