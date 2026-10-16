"""rename mixjob and repatjob status datatypes

Revision ID: 297b54e12da4
Revises: e2a7c91d4b58
Create Date: 2026-10-16 16:27:32.085313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '297b54e12da4'
down_revision: Union[str, Sequence[str], None] = 'e2a7c91d4b58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("""
        ALTER TYPE productionorderjobstatus
        RENAME TO repatjobstatus
    """)

    op.execute("""
        ALTER TYPE productionordermixjobstatus
        RENAME TO mixjobstatus
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TYPE repatjobstatus
        RENAME TO productionorderjobstatus
    """)

    op.execute("""
        ALTER TYPE mixjobstatus
        RENAME TO productionordermixjobstatus
    """)
