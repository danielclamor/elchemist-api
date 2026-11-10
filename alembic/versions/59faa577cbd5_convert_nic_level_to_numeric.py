"""convert nic level to numeric

Revision ID: 59faa577cbd5
Revises: 8aee9ad90074
Create Date: 2026-11-10 16:37:21.755487

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59faa577cbd5'
down_revision: Union[str, Sequence[str], None] = '8aee9ad90074'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LEVEL_PATTERN = r'^(hit)?([0-9]{1,2}(\.[0-9])?)(mg)?$'
HIT_DEFAULT = 20
 
 
def upgrade() -> None:
    """Upgrade schema."""
    # stop with a readable list instead of a bare cast error (or a silent rounding)
    bad = op.get_bind().execute(sa.text(
        "SELECT slug || ' (' || nic_level || ')' FROM formulas WHERE nic_level !~ :pattern ORDER BY slug"
    ), {"pattern": LEVEL_PATTERN}).scalars().all()
    if bad:
        raise RuntimeError(f"nic_level doesn't fit numeric(3, 1) for: {', '.join(bad)}")
 
    op.alter_column(
        'formulas', 'nic_level',
        existing_type=sa.String(length=10),
        type_=sa.Numeric(precision=3, scale=1),
        existing_nullable=False,
        postgresql_using=(
            f"CASE WHEN nic_level ~ '^hit' THEN {HIT_DEFAULT} "
            f"ELSE regexp_replace(nic_level, '{LEVEL_PATTERN}', '\\2')::numeric END::numeric(3, 1)"
        ),
    )
 
 
def downgrade() -> None:
    """Downgrade schema."""
    # former hit formulas come back as plain "20mg" (a valid NicLevel, but no longer a hit)
    op.alter_column(
        'formulas', 'nic_level',
        existing_type=sa.Numeric(precision=3, scale=1),
        type_=sa.String(length=10),
        existing_nullable=False,
        postgresql_using="trim_scale(nic_level)::text || 'mg'",
    )
