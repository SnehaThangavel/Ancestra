"""Raw photo observations and extracted EXIF/quality metadata records."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Observation(Base):
    """Raw crowdsourced photo observation model."""

    __tablename__ = "observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    monument_id = Column(UUID(as_uuid=True), ForeignKey("monuments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(64), index=True, nullable=True)
    image_url = Column(String(512), nullable=False)
    captured_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)

    # Image Quality and Triage metrics
    blur_score = Column(Float, nullable=True)
    sharpness_score = Column(Float, nullable=True)
    glare_score = Column(Float, nullable=True)
    exposure_score = Column(Float, nullable=True)
    overall_quality_score = Column(Float, nullable=True)
    is_valid_quality = Column(Boolean, default=True, nullable=False)
    resolution_width = Column(Integer, nullable=True)
    resolution_height = Column(Integer, nullable=True)

    # EXIF & Telemetry
    exif_data = Column(JSONB, nullable=True)

    # Registration & Reliability scoring
    registration_success = Column(Boolean, default=False, nullable=False)
    registration_confidence = Column(Float, nullable=True)
    reliability_score = Column(Float, nullable=True)
    reliability_factors = Column(JSONB, nullable=True)

    # Region registration
    region_id = Column(UUID(as_uuid=True), ForeignKey("regions.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    monument = relationship("Monument", back_populates="observations")
    region = relationship("Region", back_populates="observations")

    # Compatibility properties
    @property
    def exif_metadata(self):
        return self.exif_data

    @exif_metadata.setter
    def exif_metadata(self, val):
        self.exif_data = val

    @property
    def resolution_w(self):
        return self.resolution_width

    @resolution_w.setter
    def resolution_w(self, val):
        self.resolution_width = val

    @property
    def resolution_h(self):
        return self.resolution_height

    @resolution_h.setter
    def resolution_h(self, val):
        self.resolution_height = val
