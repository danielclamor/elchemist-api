"""rename formulas -> flavors and nic_profiles -> formulas

Revision ID: d9a4c6e2f815
Revises: SET_TO_YOUR_CURRENT_HEAD
Create Date: 2026-11-03 12:00:00.000000

Hand-written: Alembic autogenerate can't detect renames (it would drop and
recreate the tables, losing data).

Order matters. "formulas" already exists, so the old formulas table must move
out of the way (to flavors, including its primary key and index names) before
nic_profiles can take the name "formulas".
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd9a4c6e2f815'
down_revision: Union[str, Sequence[str], None] = '33fe85e28db5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# tables that point at nic_profiles (they gain a formula_id column)
CHILD_TABLES = ["eliquids", "flavorings", "nic_bases", "mix_batches"]


def _rename_table(old: str, new: str) -> None:
    op.rename_table(old, new)
    # the primary key constraint (and its index) keeps the old name unless renamed
    op.execute(f'ALTER TABLE {new} RENAME CONSTRAINT {old}_pkey TO {new}_pkey')


def _rename_column(table: str, old: str, new: str) -> None:
    op.alter_column(table, old, new_column_name=new)
    op.execute(f'ALTER INDEX IF EXISTS ix_{table}_{old} RENAME TO ix_{table}_{new}')
    op.execute(f'ALTER TABLE {table} RENAME CONSTRAINT {table}_{old}_fkey TO {table}_{new}_fkey')


def upgrade() -> None:
    # 1. formulas -> flavors
    _rename_table('formulas', 'flavors')
    op.execute('ALTER INDEX ix_formulas_slug RENAME TO ix_flavors_slug')

    # 2. nic_profiles -> formulas (its link to the old formulas becomes flavor_id)
    _rename_column('nic_profiles', 'formula_id', 'flavor_id')
    _rename_table('nic_profiles', 'formulas')
    op.execute('ALTER INDEX ix_nic_profiles_slug RENAME TO ix_formulas_slug')
    op.execute('ALTER INDEX ix_nic_profiles_flavor_id RENAME TO ix_formulas_flavor_id')
    op.execute('ALTER TABLE formulas RENAME CONSTRAINT nic_profiles_flavor_id_fkey TO formulas_flavor_id_fkey')

    # 3. everything that referenced nic_profiles
    for table in CHILD_TABLES:
        _rename_column(table, 'nic_profile_id', 'formula_id')

    op.alter_column('mix_batches', 'nic_profile_full_name_snapshot', new_column_name='formula_full_name_snapshot')


def downgrade() -> None:
    op.alter_column('mix_batches', 'formula_full_name_snapshot', new_column_name='nic_profile_full_name_snapshot')

    for table in reversed(CHILD_TABLES):
        _rename_column(table, 'formula_id', 'nic_profile_id')

    op.execute('ALTER TABLE formulas RENAME CONSTRAINT formulas_flavor_id_fkey TO nic_profiles_flavor_id_fkey')
    op.execute('ALTER INDEX ix_formulas_flavor_id RENAME TO ix_nic_profiles_flavor_id')
    op.execute('ALTER INDEX ix_formulas_slug RENAME TO ix_nic_profiles_slug')
    _rename_table('formulas', 'nic_profiles')
    _rename_column('nic_profiles', 'flavor_id', 'formula_id')

    op.execute('ALTER INDEX ix_flavors_slug RENAME TO ix_formulas_slug')
    _rename_table('flavors', 'formulas')
