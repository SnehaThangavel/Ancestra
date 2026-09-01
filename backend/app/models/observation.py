"""Raw photo observations and extracted EXIF/quality metadata records."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Observation(Base):
    """Raw crowdsourced photo observation model."""

    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    monument_id = Column(String(64), index=True, nullable=False)
    user_id = Column(String(64), index=True, nullable=True)
    image_url = Column(String(512), nullable=False)
    captured_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Image Quality and EXIF metrics
    blur_score = Column(Float, nullable=True)
    glare_score = Column(Float, nullable=True)
    resolution_w = Column(Integer, nullable=True)
    resolution_h = Column(Integer, nullable=True)
    exif_metadata = Column(JSON, nullable=True)

    # Reliability scoring
    reliability_score = Column(Float, nullable=True)
    reliability_factors = Column(JSON, nullable=True)

    # Region registration
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    region = relationship("Region", back_populates="observations")
