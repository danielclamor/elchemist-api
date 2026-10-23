"""add mix_batches

Revision ID: a3c9d7e15b82
Revises: 25d0a92034e8
Create Date: 2026-10-23 16:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a3c9d7e15b82'
down_revision: Union[str, Sequence[str], None] = '25d0a92034e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'mix_batches',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('nic_profile_id', sa.UUID(), nullable=True),
        sa.Column('nic_profile_slug_snapshot', sa.String(length=255), nullable=False),
        sa.Column(
            'status',
            sa.Enum('CANCELLED', 'COMPLETED', 'IN_PROGRESS', 'MIXED', name='mixbatchstatus'),
            nullable=False,
        ),
        sa.Column('batch_number', sa.String(length=255), nullable=True),
        sa.Column('recipe_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('total_volume_ml', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('total_weight_g', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('mixed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['nic_profile_id'], ['nic_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_mix_batches_nic_profile_id'), 'mix_batches', ['nic_profile_id'], unique=False)
    op.create_index(op.f('ix_mix_batches_status'), 'mix_batches', ['status'], unique=False)
    op.create_index(op.f('ix_mix_batches_batch_number'), 'mix_batches', ['batch_number'], unique=False)

    op.add_column('production_orders', sa.Column('mix_batch_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_production_orders_mix_batch_id'), 'production_orders', ['mix_batch_id'], unique=False)
    op.create_foreign_key(
        'production_orders_mix_batch_id_fkey',
        'production_orders',
        'mix_batches',
        ['mix_batch_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('production_orders_mix_batch_id_fkey', 'production_orders', type_='foreignkey')
    op.drop_index(op.f('ix_production_orders_mix_batch_id'), table_name='production_orders')
    op.drop_column('production_orders', 'mix_batch_id')

    op.drop_index(op.f('ix_mix_batches_batch_number'), table_name='mix_batches')
    op.drop_index(op.f('ix_mix_batches_status'), table_name='mix_batches')
    op.drop_index(op.f('ix_mix_batches_nic_profile_id'), table_name='mix_batches')
    op.drop_table('mix_batches')
    op.execute('DROP TYPE mixbatchstatus')
