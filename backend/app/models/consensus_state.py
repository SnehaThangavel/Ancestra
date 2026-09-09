"""Per-region consensus memory state and Bayesian running update representations."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class ConsensusState(Base):
    """Consensus state memory tracking running structural condition per region."""

    __tablename__ = "consensus_states"
    __table_args__ = (
        CheckConstraint(
            "structural_health_index >= 0.0 AND structural_health_index <= 1.0",
            name="check_structural_health_index",
        ),
        UniqueConstraint("region_id", "version", name="uq_consensus_states_region_version"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_id = Column(
        UUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version = Column(Integer, default=1, nullable=False)
    consensus_tensor = Column(JSONB, nullable=True)  # feature tensor / baseline representation
    cumulative_reliability = Column(Float, default=0.0, nullable=False)
    observation_count = Column(Integer, default=0, nullable=False)
    structural_health_index = Column(Float, default=1.0, nullable=False)  # 1.0 (pristine) -> 0.0 (critical)
    last_updated_by_observation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("observations.id", ondelete="SET NULL"),
        nullable=True,
    )
    reset_reason = Column(String(512), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=func.now(),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    region = relationship("Region", back_populates="consensus_states")
    last_updated_by_observation = relationship("Observation", foreign_keys=[last_updated_by_observation_id])

    # Compatibility properties
    @property
    def state_vector(self):
        return self.consensus_tensor

    @state_vector.setter
    def state_vector(self, value):
        self.consensus_tensor = value

    @property
    def last_updated(self):
        return self.updated_at

    @last_updated.setter
    def last_updated(self, value):
        self.updated_at = value
