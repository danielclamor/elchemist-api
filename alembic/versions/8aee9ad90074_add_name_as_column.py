"""add full_name as column

Revision ID: 8aee9ad90074
Revises: 28296ab9b4a9
Create Date: 2026-11-10 16:06:51.593585

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8aee9ad90074'
down_revision: Union[str, Sequence[str], None] = '28296ab9b4a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # nullable first, so the existing rows can be filled before it becomes required
    op.add_column('formulas', sa.Column('name', sa.String(length=255), nullable=True))
 
    # nic_type is stored as the enum name (SALT / FREEBASE); initcap gives Salt / Freebase,
    # the same as NicType.value.title() in Python
    op.execute("""
        UPDATE formulas
        SET name = brand || ' ' || flavor_name || ' ' || initcap(nic_type::text) || CASE WHEN is_old_mix THEN ' Old Mix' ELSE '' END || ' ' || nic_level
    """)
 
    op.alter_column('formulas', 'name', existing_type=sa.String(length=255), nullable=False)
 
 
def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('formulas', 'name')
