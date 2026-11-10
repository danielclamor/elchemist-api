"""delete flavor table

Revision ID: 6161c17eb912
Revises: 8254ba5f2a07
Create Date: 2026-11-10 15:11:52.691511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6161c17eb912'
down_revision: Union[str, Sequence[str], None] = '8254ba5f2a07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
