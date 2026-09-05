"""initial postgresql schema with uuid and jsonb

Revision ID: f6227ed998c5
Revises: 
Create Date: 2026-09-05 15:05:59.888425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6227ed998c5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Monuments table
    op.create_table(
        'monuments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location_name', sa.String(length=255), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('heritage_status', sa.String(length=128), nullable=True),
        sa.Column('importance_tier', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Regions table
    op.create_table(
        'regions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('monument_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=True),
        sa.Column('bounding_box', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('reference_features', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['monument_id'], ['monuments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_regions_monument_id'), 'regions', ['monument_id'], unique=False)

    # 3. Anomaly Validations table
    op.create_table(
        'anomaly_validations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('region_id', sa.UUID(), nullable=False),
        sa.Column('anomaly_type', sa.String(length=64), nullable=False),
        sa.Column('ssim_delta', sa.Float(), nullable=True),
        sa.Column('severity_score', sa.Float(), nullable=False),
        sa.Column('corroboration_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('corroborating_observation_ids', postgresql.ARRAY(sa.UUID()), nullable=True),
        sa.Column('is_confirmed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('defect_polygon', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('severity_score >= 0.0 AND severity_score <= 1.0', name='check_severity_score'),
        sa.ForeignKeyConstraint(['region_id'], ['regions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_anomaly_validations_region_id'), 'anomaly_validations', ['region_id'], unique=False)

    # 4. Consensus States table
    op.create_table(
        'consensus_states',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('region_id', sa.UUID(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('consensus_tensor', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('cumulative_reliability', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('observation_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('structural_health_index', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('structural_health_index >= 0.0 AND structural_health_index <= 1.0', name='check_structural_health_index'),
        sa.ForeignKeyConstraint(['region_id'], ['regions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consensus_states_region_id'), 'consensus_states', ['region_id'], unique=False)

    # 5. Observations table
    op.create_table(
        'observations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('monument_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=True),
        sa.Column('image_url', sa.String(length=512), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('blur_score', sa.Float(), nullable=True),
        sa.Column('sharpness_score', sa.Float(), nullable=True),
        sa.Column('glare_score', sa.Float(), nullable=True),
        sa.Column('exposure_score', sa.Float(), nullable=True),
        sa.Column('overall_quality_score', sa.Float(), nullable=True),
        sa.Column('is_valid_quality', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('resolution_width', sa.Integer(), nullable=True),
        sa.Column('resolution_height', sa.Integer(), nullable=True),
        sa.Column('exif_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('registration_success', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('registration_confidence', sa.Float(), nullable=True),
        sa.Column('reliability_score', sa.Float(), nullable=True),
        sa.Column('reliability_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('region_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['monument_id'], ['monuments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['region_id'], ['regions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_observations_monument_id'), 'observations', ['monument_id'], unique=False)
    op.create_index(op.f('ix_observations_region_id'), 'observations', ['region_id'], unique=False)
    op.create_index(op.f('ix_observations_user_id'), 'observations', ['user_id'], unique=False)
    # GIN index on observations.exif_data
    op.create_index('idx_observations_exif_data_gin', 'observations', ['exif_data'], postgresql_using='gin')

    # 6. Work Orders table
    op.create_table(
        'work_orders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('validation_id', sa.UUID(), nullable=False),
        sa.Column('urgency_index', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('assigned_team', sa.String(length=128), nullable=True),
        sa.Column('recommended_action', sa.String(length=256), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('urgency_index >= 0.0 AND urgency_index <= 1.0', name='check_urgency_index'),
        sa.ForeignKeyConstraint(['validation_id'], ['anomaly_validations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_work_orders_validation_id'), 'work_orders', ['validation_id'], unique=False)

    # 7. Evidence Logs table
    op.create_table(
        'evidence_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('work_order_id', sa.UUID(), nullable=False),
        sa.Column('block_index', sa.Integer(), nullable=False),
        sa.Column('previous_hash', sa.String(length=64), nullable=False),
        sa.Column('current_hash', sa.String(length=64), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('work_order_id', 'block_index', name='uq_evidence_logs_work_order_block')
    )
    op.create_index(op.f('ix_evidence_logs_work_order_id'), 'evidence_logs', ['work_order_id'], unique=False)

    # Triggers for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    op.execute("CREATE TRIGGER trg_monuments_updated_at BEFORE UPDATE ON monuments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")
    op.execute("CREATE TRIGGER trg_regions_updated_at BEFORE UPDATE ON regions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")
    op.execute("CREATE TRIGGER trg_anomaly_validations_updated_at BEFORE UPDATE ON anomaly_validations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")
    op.execute("CREATE TRIGGER trg_consensus_states_updated_at BEFORE UPDATE ON consensus_states FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")
    op.execute("CREATE TRIGGER trg_work_orders_updated_at BEFORE UPDATE ON work_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_work_orders_updated_at ON work_orders;")
    op.execute("DROP TRIGGER IF EXISTS trg_consensus_states_updated_at ON consensus_states;")
    op.execute("DROP TRIGGER IF EXISTS trg_anomaly_validations_updated_at ON anomaly_validations;")
    op.execute("DROP TRIGGER IF EXISTS trg_regions_updated_at ON regions;")
    op.execute("DROP TRIGGER IF EXISTS trg_monuments_updated_at ON monuments;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")

    op.drop_index(op.f('ix_evidence_logs_work_order_id'), table_name='evidence_logs')
    op.drop_table('evidence_logs')
    op.drop_index(op.f('ix_work_orders_validation_id'), table_name='work_orders')
    op.drop_table('work_orders')
    op.drop_index('idx_observations_exif_data_gin', table_name='observations', postgresql_using='gin')
    op.drop_index(op.f('ix_observations_user_id'), table_name='observations')
    op.drop_index(op.f('ix_observations_region_id'), table_name='observations')
    op.drop_index(op.f('ix_observations_monument_id'), table_name='observations')
    op.drop_table('observations')
    op.drop_index(op.f('ix_consensus_states_region_id'), table_name='consensus_states')
    op.drop_table('consensus_states')
    op.drop_index(op.f('ix_anomaly_validations_region_id'), table_name='anomaly_validations')
    op.drop_table('anomaly_validations')
    op.drop_index(op.f('ix_regions_monument_id'), table_name='regions')
    op.drop_table('regions')
    op.drop_table('monuments')
