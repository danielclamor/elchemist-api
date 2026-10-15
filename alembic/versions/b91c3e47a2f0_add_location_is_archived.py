"""add location is_archived

Revision ID: b91c3e47a2f0
Revises: d7bc0d2048da
Create Date: 2026-10-15 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b91c3e47a2f0'
down_revision: Union[str, Sequence[str], None] = 'd7bc0d2048da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  op.add_column(
    "locations",
    sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
  )

def downgrade() -> None:
  op.drop_column("locations", "is_archived")
