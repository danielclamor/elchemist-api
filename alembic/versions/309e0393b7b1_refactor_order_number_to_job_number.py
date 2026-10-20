"""refactor order number to job number

Revision ID: 309e0393b7b1
Revises: 297b54e12da4
Create Date: 2026-10-20 14:37:54.419074

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '309e0393b7b1'
down_revision: Union[str, Sequence[str], None] = '297b54e12da4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = [("mix_jobs", "MJ"), ("repat_jobs", "RJ")]

def upgrade() -> None:
  for table, prefix in TABLES:
    op.drop_index(f"ix_{table}_production_order_number", table_name=table)

    op.alter_column(
      table, "production_order_number",
      new_column_name="job_number",
      existing_type=sa.String(length=20), type_=sa.String(length=32),
      existing_nullable=False,
    )

    op.execute(f"""
      UPDATE {table} AS j
      SET job_number = po.order_number || '-{prefix}' || r.n
      FROM (
        SELECT id, production_order_id,
               ROW_NUMBER() OVER (PARTITION BY production_order_id ORDER BY created_at, id) AS n
        FROM {table}
      ) AS r
      JOIN production_orders AS po ON po.id = r.production_order_id
      WHERE j.id = r.id
    """)

    op.create_index(f"ix_{table}_job_number", table, ["job_number"], unique=True)


def downgrade() -> None:
  for table, _prefix in TABLES:
    op.drop_index(f"ix_{table}_job_number", table_name=table)
    op.execute(f"""
      UPDATE {table} AS j SET job_number = po.order_number
      FROM production_orders AS po WHERE po.id = j.production_order_id
    """)
    op.alter_column(
      table, "job_number", new_column_name="production_order_number",
      existing_type=sa.String(length=32), type_=sa.String(length=20),
      existing_nullable=False,
    )
    op.create_index(f"ix_{table}_production_order_number", table, ["production_order_number"], unique=False)
