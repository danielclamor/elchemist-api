"""remove ASSIGN_JOB value

Revision ID: 5e25136b33ff
Revises: a998c764e437
Create Date: 2026-11-11 11:58:03.576222

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e25136b33ff'
down_revision: Union[str, Sequence[str], None] = 'a998c764e437'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE production_order_activity_logs
        SET type = 'ASSIGN_MIX_BATCH'
        WHERE type = 'ASSIGN_JOB'
    """)

    op.execute("ALTER TYPE productionorderactivitytype RENAME TO productionorderactivitytypeold")

    op.execute("CREATE TYPE productionorderactivitytype AS ENUM('CREATED', 'ADJUST_QUANTITY', 'CHANGE_STATUS', 'SWITCH_PRIORITY', 'TOGGLE_ARCHIVED', 'ASSIGN_MIX_BATCH')")

    op.execute("""
        ALTER TABLE production_order_activity_logs
        ALTER COLUMN type TYPE productionorderactivitytype
        USING type::text::productionorderactivitytype
    """)

    op.execute("DROP TYPE productionorderactivitytypeold")


def downgrade() -> None:
    op.execute("ALTER TYPE productionorderactivitytype ADD VALUE IF NOT EXISTS 'ASSIGN_JOB'")
