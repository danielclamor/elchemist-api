"""rename activity to activity type

Revision ID: da0a8414bd60
Revises: ccf17f4d1019
Create Date: 2026-10-09 12:59:01.113719

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'da0a8414bd60'
down_revision: Union[str, Sequence[str], None] = 'ccf17f4d1019'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

activity_type = postgresql.ENUM('CREATED', 'ADJUST_QUANTITY', 'CHANGE_STATUS', 'SWITCH_PRIORITY', 'TOGGLE_ARCHIVED', 'ASSIGN_JOB', name='productionorderactivitytype')

def upgrade() -> None:
    bind = op.get_bind()
    activity_type.create(bind, checkfirst=True)
    
    op.add_column('production_order_activity_logs', sa.Column(
      'type',
      postgresql.ENUM(name='productionorderactivitytype', create_type=False),
      nullable=True,
    ))
    op.execute("UPDATE production_order_activity_logs SET type = activity::text::productionorderactivitytype")
    op.alter_column('production_order_activity_logs', 'type')
    op.drop_column('production_order_activity_logs', 'activity')
    
    op.execute("DROP TYPE productionorderactivity")
