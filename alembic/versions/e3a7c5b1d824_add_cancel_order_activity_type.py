"""add CANCEL_ORDER to production order activity type

Revision ID: e3a7c5b1d824
Revises: 81910658c274
Create Date: 2026-11-17 17:05:00.000000

Postgres can't use a new enum value in the transaction that adds it, so the
ADD VALUE runs in an autocommit block. Downgrade rebuilds the type without
CANCEL_ORDER; existing CANCEL_ORDER log rows become CHANGE_STATUS.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'e3a7c5b1d824'
down_revision: Union[str, Sequence[str], None] = '81910658c274'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE productionorderactivitytype ADD VALUE IF NOT EXISTS 'CANCEL_ORDER'")


def downgrade() -> None:
    op.execute("ALTER TYPE productionorderactivitytype RENAME TO productionorderactivitytype_old")
    op.execute(
        "CREATE TYPE productionorderactivitytype AS ENUM "
        "('CREATED', 'ADJUST_QUANTITY', 'CHANGE_STATUS', 'SWITCH_PRIORITY', "
        "'TOGGLE_ARCHIVED', 'ASSIGN_MIX_SESSION')"
    )
    op.execute(
        "ALTER TABLE production_order_activity_logs ALTER COLUMN type "
        "TYPE productionorderactivitytype USING "
        "(CASE type::text WHEN 'CANCEL_ORDER' THEN 'CHANGE_STATUS' ELSE type::text END)"
        "::productionorderactivitytype"
    )
    op.execute("DROP TYPE productionorderactivitytype_old")
