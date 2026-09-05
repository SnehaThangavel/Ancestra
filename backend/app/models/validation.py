"""Validated anomaly findings and structural defect records."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class AnomalyValidation(Base):
    """Validated structural anomaly record."""

    __tablename__ = "anomaly_validations"
    __table_args__ = (
        CheckConstraint(
            "severity_score >= 0.0 AND severity_score <= 1.0",
            name="check_severity_score",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_id = Column(
        UUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    anomaly_type = Column(String(64), nullable=False)  # crack, spalling, biological_growth, discoloration
    ssim_delta = Column(Float, nullable=True)
    severity_score = Column(Float, nullable=False)  # 0.0 to 1.0
    corroboration_count = Column(Integer, default=1, nullable=False)
    corroborating_observation_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    is_confirmed = Column(Boolean, default=False, nullable=False)
    defect_polygon = Column(JSONB, nullable=True)  # polygon / bounding coordinates of defect
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
    region = relationship("Region", back_populates="validations")
    work_orders = relationship("WorkOrder", back_populates="validation", cascade="all, delete-orphan")

    # Compatibility properties
    @property
    def mask_geometry(self):
        return self.defect_polygon

    @mask_geometry.setter
    def mask_geometry(self, value):
        self.defect_polygon = value
