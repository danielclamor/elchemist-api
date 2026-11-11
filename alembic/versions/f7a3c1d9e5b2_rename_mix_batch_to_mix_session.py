"""rename mix_batch to mix_session

Revision ID: f7a3c1d9e5b2
Revises: 5e25136b33ff
Create Date: 2026-11-11 14:00:00.000000

Hand-written: Alembic autogenerate can't detect renames (it would drop and recreate
the tables and lose the data). Renames, with no data change:
  tables   mix_batches -> mix_sessions, mix_batch_counter -> mix_session_counter
  column   production_orders.mix_batch_id -> mix_session_id
  enum     mixbatchstatus -> mixsessionstatus
  value    productionorderactivitytype 'ASSIGN_MIX_BATCH' -> 'ASSIGN_MIX_SESSION'
  plus the primary keys, foreign keys and indexes that carry the old name.
batch_code (the lot code printed on the bottles) and mix_number keep their names.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f7a3c1d9e5b2'
down_revision: Union[str, Sequence[str], None] = '5e25136b33ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _run(reverse: bool) -> None:
    """Apply every rename, or undo it all when reverse is True."""
    def pick(old: str, new: str) -> tuple[str, str]:
        return (new, old) if reverse else (old, new)

    # enum type and the activity-log value
    a, b = pick("mixbatchstatus", "mixsessionstatus")
    op.execute(f"ALTER TYPE {a} RENAME TO {b}")
    a, b = pick("ASSIGN_MIX_BATCH", "ASSIGN_MIX_SESSION")
    op.execute(f"ALTER TYPE productionorderactivitytype RENAME VALUE '{a}' TO '{b}'")

    # mix_batches -> mix_sessions: table, primary key, indexes, foreign key
    old_t, new_t = pick("mix_batches", "mix_sessions")
    op.rename_table(old_t, new_t)
    for suffix in ("pkey",):
        a, b = pick(f"mix_batches_{suffix}", f"mix_sessions_{suffix}")
        op.execute(f"ALTER TABLE {new_t} RENAME CONSTRAINT {a} TO {b}")
    for column in ("formula_id", "mix_number", "status"):
        a, b = pick(f"ix_mix_batches_{column}", f"ix_mix_sessions_{column}")
        op.execute(f"ALTER INDEX {a} RENAME TO {b}")
    a, b = pick("mix_batches_formula_id_fkey", "mix_sessions_formula_id_fkey")
    op.execute(f"ALTER TABLE {new_t} RENAME CONSTRAINT {a} TO {b}")

    # mix_batch_counter -> mix_session_counter
    old_t, new_t = pick("mix_batch_counter", "mix_session_counter")
    op.rename_table(old_t, new_t)
    a, b = pick("mix_batch_counter_pkey", "mix_session_counter_pkey")
    op.execute(f"ALTER TABLE {new_t} RENAME CONSTRAINT {a} TO {b}")

    # production_orders.mix_batch_id -> mix_session_id
    a, b = pick("mix_batch_id", "mix_session_id")
    op.alter_column("production_orders", a, new_column_name=b)
    a, b = pick("ix_production_orders_mix_batch_id", "ix_production_orders_mix_session_id")
    op.execute(f"ALTER INDEX {a} RENAME TO {b}")
    a, b = pick("production_orders_mix_batch_id_fkey", "production_orders_mix_session_id_fkey")
    op.execute(f"ALTER TABLE production_orders RENAME CONSTRAINT {a} TO {b}")


def upgrade() -> None:
    _run(reverse=False)


def downgrade() -> None:
    _run(reverse=True)
