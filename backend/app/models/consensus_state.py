"""Per-region consensus memory state and Bayesian running update representations."""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class ConsensusState(Base):
    """Consensus state memory tracking running structural condition per region."""

    __tablename__ = "consensus_states"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    state_vector = Column(JSON, nullable=True)  # feature tensor / baseline representation
    cumulative_reliability = Column(Float, default=0.0, nullable=False)
    observation_count = Column(Integer, default=0, nullable=False)
    structural_health_index = Column(Float, default=1.0, nullable=False)  # 1.0 (pristine) -> 0.0 (critical)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)

    region = relationship("Region", back_populates="consensus_states")
