"""rename job to jobtype

Revision ID: c4a9ee5fd5be
Revises: b91c3e47a2f0
Create Date: 2026-10-16 10:10:13.616402

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c4a9ee5fd5be'
down_revision: Union[str, Sequence[str], None] = 'b91c3e47a2f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

job_type = postgresql.ENUM('MIX', 'REPAT', name='productionorderjobtype')

def upgrade() -> None:
    bind = op.get_bind()
    job_type.create(bind, checkfirst=True)
    
    op.add_column('production_orders', sa.Column(
      'job_type',
      postgresql.ENUM(name='productionorderjobtype', create_type=False),
      nullable=True,
    ))
    op.execute('UPDATE production_orders SET job_type = job::text::productionorderjobtype')
    op.alter_column('production_orders', 'job_type')
    op.drop_column('production_orders', 'job')
    
    op.execute('DROP TYPE productionorderjob')


def downgrade() -> None:
    """Downgrade schema."""
    pass
