"""rename production_order_mix_jobs / production_order_repat_jobs to mix_jobs / repat_jobs

Revision ID: e2a7c91d4b58
Revises: c4a9ee5fd5be
Create Date: 2026-10-16 15:10:00.000000

Pure renames: no data is copied or dropped. The Postgres enum types
(productionordermixjobstatus, productionorderjobstatus) keep their names.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e2a7c91d4b58'
down_revision: Union[str, Sequence[str], None] = 'c4a9ee5fd5be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (old table, new table, [(old index, new index), ...])
RENAMES = [
  (
    "production_order_mix_jobs",
    "mix_jobs",
    [
      ("production_order_mix_jobs_pkey", "mix_jobs_pkey"),
      ("ix_production_order_mix_jobs_one_active_per_order", "ix_mix_jobs_one_active_per_order"),
      ("ix_production_order_mix_jobs_production_order_id", "ix_mix_jobs_production_order_id"),
      ("ix_production_order_mix_jobs_production_order_number", "ix_mix_jobs_production_order_number"),
    ],
  ),
  (
    "production_order_repat_jobs",
    "repat_jobs",
    [
      ("production_order_repat_jobs_pkey", "repat_jobs_pkey"),
      ("ix_production_order_repat_jobs_one_active_per_order", "ix_repat_jobs_one_active_per_order"),
      ("ix_production_order_repat_jobs_production_order_id", "ix_repat_jobs_production_order_id"),
      ("ix_production_order_repat_jobs_production_order_number", "ix_repat_jobs_production_order_number"),
    ],
  ),
]


def upgrade() -> None:
  for old_table, new_table, indexes in RENAMES:
    op.rename_table(old_table, new_table)
    for old_index, new_index in indexes:
      op.execute(f'ALTER INDEX IF EXISTS "{old_index}" RENAME TO "{new_index}"')


def downgrade() -> None:
  for old_table, new_table, indexes in RENAMES:
    for old_index, new_index in indexes:
      op.execute(f'ALTER INDEX IF EXISTS "{new_index}" RENAME TO "{old_index}"')
    op.rename_table(new_table, old_table)
