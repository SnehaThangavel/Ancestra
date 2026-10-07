"""Architectural region records and monument geometry segments."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Region(Base):
    """Architectural region / structural component model."""

    __tablename__ = "regions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    monument_id = Column(UUID(as_uuid=True), ForeignKey("monuments.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=True)  # pillar, arch, facade, frieze, dome
    image_url = Column(String(512), nullable=True)
    bounding_box = Column(JSONB, nullable=True)  # [x, y, w, h] or polygon coordinates
    reference_features = Column(JSONB, nullable=True)  # keypoint descriptors / reference embeddings
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=func.now(), server_default=func.now(), nullable=False)

    # Relationships
    monument = relationship("Monument", back_populates="regions")
    observations = relationship("Observation", back_populates="region")
    consensus_states = relationship("ConsensusState", back_populates="region", cascade="all, delete-orphan")
    validations = relationship("AnomalyValidation", back_populates="region", cascade="all, delete-orphan")
