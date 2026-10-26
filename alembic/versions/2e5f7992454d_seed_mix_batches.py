"""seed mix_batches

Revision ID: 2e5f7992454d
Revises: 7e68f35084b9
Create Date: 2026-10-26 11:27:18.199481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e5f7992454d'
down_revision: Union[str, Sequence[str], None] = '7e68f35084b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # batch ids were copied from mix_jobs ids by the earlier backfill,
    # so they join back one-to-one
    op.execute("""
        UPDATE mix_batches AS b
        SET mix_number = j.job_number
        FROM mix_jobs AS j
        WHERE j.id = b.id AND b.mix_number IS NULL
    """)
    op.execute("""
        UPDATE mix_batches AS b
        SET batch_code = j.batch_number
        FROM mix_jobs AS j
        WHERE j.id = b.id AND b.batch_code IS NULL AND j.batch_number IS NOT NULL
    """)


def downgrade() -> None:
    pass  # populated data isn't worth reversing
