"""add CUSTOM to niclevel

Revision ID: b5c8e2d7f136
Revises: a7d3e9b1c540
Create Date: 2026-11-25 16:50:00.000000

Postgres can't use a new enum value in the transaction that adds it, so the
ADD VALUE runs in an autocommit block.
Downgrade refuses to run while any eliquid still uses CUSTOM.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b5c8e2d7f136'
down_revision: Union[str, Sequence[str], None] = 'a7d3e9b1c540'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE niclevel ADD VALUE IF NOT EXISTS 'CUSTOM'")


def downgrade() -> None:
    in_use = op.get_bind().execute(
        sa.text("SELECT count(*) FROM eliquids WHERE nic_level::text = 'CUSTOM'")
    ).scalar()
    if in_use:
        raise RuntimeError(f"Cannot remove CUSTOM: {in_use} eliquid(s) still use it")

    op.execute("ALTER TYPE niclevel RENAME TO niclevel_old")
    op.execute(
        "CREATE TYPE niclevel AS ENUM "
        "('MG_0', 'MG_3', 'MG_5', 'MG_6', 'MG_10', 'MG_12', 'MG_15', 'MG_18', 'MG_20', 'HIT_35', 'HIT_50')"
    )
    op.execute(
        "ALTER TABLE eliquids ALTER COLUMN nic_level "
        "TYPE niclevel USING nic_level::text::niclevel"
    )
    op.execute("DROP TYPE niclevel_old")
