"""add consensus state columns and unique constraint

Revision ID: a1b2c3d4e5f6
Revises: 9944267301e9
Create Date: 2026-09-09 14:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9944267301e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add last_updated_by_observation_id and reset_reason columns to consensus_states
    op.add_column('consensus_states', sa.Column('last_updated_by_observation_id', sa.UUID(), nullable=True))
    op.add_column('consensus_states', sa.Column('reset_reason', sa.String(length=512), nullable=True))
    op.create_foreign_key(
        'fk_consensus_states_last_updated_obs',
        'consensus_states',
        'observations',
        ['last_updated_by_observation_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_unique_constraint(
        'uq_consensus_states_region_version',
        'consensus_states',
        ['region_id', 'version']
    )


def downgrade() -> None:
    op.drop_constraint('uq_consensus_states_region_version', 'consensus_states', type_='unique')
    op.drop_constraint('fk_consensus_states_last_updated_obs', 'consensus_states', type_='foreignkey')
    op.drop_column('consensus_states', 'reset_reason')
    op.drop_column('consensus_states', 'last_updated_by_observation_id')
