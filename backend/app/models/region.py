"""Architectural region records and monument geometry segments."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Region(Base):
    """Architectural region / structural component model."""

    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    monument_id = Column(String(64), index=True, nullable=False)
    name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=True)  # pillar, arch, facade, frieze, dome
    bounding_box = Column(JSON, nullable=True)  # [x, y, w, h] or polygon coordinates
    reference_features = Column(JSON, nullable=True)  # keypoint descriptors / reference embedding
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    observations = relationship("Observation", back_populates="region")
    consensus_states = relationship("ConsensusState", back_populates="region")
    validations = relationship("AnomalyValidation", back_populates="region")
