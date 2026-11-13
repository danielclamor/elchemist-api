"""mix session status: only IN_PROGRESS and MIXED

Revision ID: c6d2e8a4f917
Revises: b4e8d1f6a203
Create Date: 2026-11-13 17:30:00.000000

Cancelling a session now means deleting it, and COMPLETED is folded into MIXED.
  - CANCELLED sessions are deleted (their orders were already detached; any that
    are not get mix_session_id = NULL through the FK's ondelete SET NULL)
  - COMPLETED sessions become MIXED
  - the enum type is rebuilt with just IN_PROGRESS and MIXED
Downgrade restores the four values (deleted sessions cannot come back).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c6d2e8a4f917'
down_revision: Union[str, Sequence[str], None] = 'b4e8d1f6a203'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _swap_enum(values: tuple[str, ...]) -> None:
    op.execute("ALTER TYPE mixsessionstatus RENAME TO mixsessionstatus_old")
    labels = ", ".join(f"'{v}'" for v in values)
    op.execute(f"CREATE TYPE mixsessionstatus AS ENUM ({labels})")
    op.execute(
        "ALTER TABLE mix_sessions ALTER COLUMN status "
        "TYPE mixsessionstatus USING status::text::mixsessionstatus"
    )
    op.execute("DROP TYPE mixsessionstatus_old")


def upgrade() -> None:
    op.execute("DELETE FROM mix_sessions WHERE status::text = 'CANCELLED'")
    op.execute("UPDATE mix_sessions SET status = 'MIXED' WHERE status::text = 'COMPLETED'")
    _swap_enum(('IN_PROGRESS', 'MIXED'))


def downgrade() -> None:
    _swap_enum(('CANCELLED', 'COMPLETED', 'IN_PROGRESS', 'MIXED'))
