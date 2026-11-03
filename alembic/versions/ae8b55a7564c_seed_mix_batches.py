"""seed mix_batches

Revision ID: ae8b55a7564c
Revises: 7e68f35084b9
Create Date: 2026-10-26 11:33:34.660534

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae8b55a7564c'
down_revision: Union[str, Sequence[str], None] = '7e68f35084b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # one batch per mix job, reusing the job's id
    op.execute("""
        INSERT INTO mix_batches (
            id, mix_number, nic_profile_id, nic_profile_slug_snapshot, status, batch_code,
            recipe_snapshot, total_volume_ml, total_weight_g, mixed_at, created_at, updated_at
        )
        SELECT
            j.id,
            j.job_number,
            np.id,
            COALESCE(np.slug, 'unknown'),
            (CASE j.status::text WHEN 'REASSIGNED' THEN 'CANCELLED' ELSE j.status::text END)::mixbatchstatus,
            j.batch_number,
            j.recipe_snapshot,
            j.total_volume_ml,
            j.total_weight_g,
            CASE WHEN j.status::text IN ('MIXED', 'COMPLETED') THEN j.updated_at END,
            j.created_at,
            j.updated_at
        FROM mix_jobs AS j
        JOIN production_orders AS po ON po.id = j.production_order_id
        JOIN eliquids AS e ON e.id = po.eliquid_id
        LEFT JOIN nic_profiles AS np ON np.id = e.nic_profile_id
    """)

    # link each PO to its live or completed batch
    op.execute("""
        UPDATE production_orders AS po
        SET mix_batch_id = pick.id
        FROM (
            SELECT DISTINCT ON (production_order_id) id, production_order_id
            FROM mix_jobs
            WHERE status::text IN ('IN_PROGRESS', 'MIXED', 'COMPLETED')
            ORDER BY production_order_id, (status::text = 'COMPLETED'), created_at DESC, id
        ) AS pick
        WHERE po.id = pick.production_order_id
    """)

    # model has mix_number NOT NULL; skip this line if your earlier migration already did it
    op.alter_column('mix_batches', 'mix_number', existing_type=sa.String(length=32), nullable=False)


def downgrade() -> None:
    op.alter_column('mix_batches', 'mix_number', existing_type=sa.String(length=32), nullable=True)
    op.execute("UPDATE production_orders SET mix_batch_id = NULL WHERE mix_batch_id IN (SELECT id FROM mix_jobs)")
    op.execute("DELETE FROM mix_batches WHERE id IN (SELECT id FROM mix_jobs)")