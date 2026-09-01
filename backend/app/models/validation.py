"""Validated anomaly findings and structural defect records."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class AnomalyValidation(Base):
    """Validated structural anomaly record."""

    __tablename__ = "anomaly_validations"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    anomaly_type = Column(String(64), nullable=False)  # crack, spalling, biological_growth, discoloration
    ssim_delta = Column(Float, nullable=True)
    severity_score = Column(Float, nullable=False)  # 0.0 to 1.0
    corroboration_count = Column(Integer, default=1, nullable=False)
    is_confirmed = Column(Boolean, default=False, nullable=False)
    mask_geometry = Column(JSON, nullable=True)  # polygon / bounding coordinates of defect
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    region = relationship("Region", back_populates="validations")
    work_orders = relationship("WorkOrder", back_populates="validation")
