"""add_baseline_observation_id_to_consensus_states

Revision ID: 83c8e76e8d92
Revises: a1b2c3d4e5f6
Create Date: 2026-09-27 21:57:24.698896

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83c8e76e8d92'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('consensus_states', sa.Column('baseline_observation_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_consensus_states_baseline_obs',
        'consensus_states',
        'observations',
        ['baseline_observation_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_consensus_states_baseline_obs', 'consensus_states', type_='foreignkey')
    op.drop_column('consensus_states', 'baseline_observation_id')
