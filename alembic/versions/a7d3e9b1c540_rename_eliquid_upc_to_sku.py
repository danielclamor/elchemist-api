"""rename eliquids.upc to sku and widen it to 100 characters

Revision ID: a7d3e9b1c540
Revises: f1c9a3e7b258
Create Date: 2026-11-25 16:40:00.000000

Column + index rename and a longer String; no data changes. (Autogenerate
would drop and re-add the column, losing the data.)
Downgrade refuses to run if any sku is longer than 12 characters.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7d3e9b1c540'
down_revision: Union[str, Sequence[str], None] = 'f1c9a3e7b258'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('eliquids', 'upc', new_column_name='sku',
                    existing_type=sa.String(length=12), type_=sa.String(length=100),
                    existing_nullable=False)
    op.execute("ALTER INDEX ix_eliquids_upc RENAME TO ix_eliquids_sku")


def downgrade() -> None:
    too_long = op.get_bind().execute(
        sa.text("SELECT sku FROM eliquids WHERE length(sku) > 12 ORDER BY sku")
    ).scalars().all()
    if too_long:
        raise RuntimeError(f"Cannot shorten sku to 12 characters; too long: {too_long}")

    op.execute("ALTER INDEX ix_eliquids_sku RENAME TO ix_eliquids_upc")
    op.alter_column('eliquids', 'sku', new_column_name='upc',
                    existing_type=sa.String(length=100), type_=sa.String(length=12),
                    existing_nullable=False)
