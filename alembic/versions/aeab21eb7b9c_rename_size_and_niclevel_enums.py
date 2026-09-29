"""rename size and niclevel enums

Revision ID: aeab21eb7b9c
Revises: 7cf366993a88
Create Date: 2026-09-29 09:45:39.846173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'aeab21eb7b9c'
down_revision: Union[str, Sequence[str], None] = '7cf366993a88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.dialects import postgresql

bottle_size = postgresql.ENUM('ML_30', 'ML_60', 'ML_120', name='bottlesize')
nic_level = postgresql.ENUM(
    'MG_0', 'MG_3', 'MG_5', 'MG_6', 'MG_10', 'MG_12',
    'MG_15', 'MG_18', 'MG_20', 'HIT_35', 'HIT_50', name='niclevel',
)

def upgrade() -> None:
    bind = op.get_bind()
    bottle_size.create(bind, checkfirst=True)
    nic_level.create(bind, checkfirst=True)

    op.add_column('eliquids', sa.Column(
        'bottle_size',
        postgresql.ENUM(name='bottlesize', create_type=False),
        nullable=True,
    ))
    op.execute("UPDATE eliquids SET bottle_size = size::text::bottlesize")
    op.alter_column('eliquids', 'bottle_size', nullable=False)
    op.drop_column('eliquids', 'size')

    op.execute(
        "ALTER TABLE eliquids ALTER COLUMN nic_level "
        "TYPE niclevel USING nic_level::text::niclevel"
    )
    op.execute("DROP TYPE sizeoption")
    op.execute("DROP TYPE nicleveloption")
