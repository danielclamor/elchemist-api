"""seed flavor fields in formula

Revision ID: 8254ba5f2a07
Revises: a2ceca6696e6
Create Date: 2026-11-10 14:54:40.841189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8254ba5f2a07'
down_revision: Union[str, Sequence[str], None] = 'a2ceca6696e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE formulas
        SET brand = flavors.brand,
            chill_type = flavors.chill_type,
            nic_type = flavors.nic_type
        FROM flavors
        WHERE formulas.flavor_id = flavors.id
    """)
    


def downgrade() -> None:
    op.execute("""
        UPDATE formulas
        SET brand = NULL,
            chill_type = NULL,
            nic_type = NULL
    """)
