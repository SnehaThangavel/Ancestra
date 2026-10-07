"""Monument architectural model representing monitored heritage sites."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Monument(Base):
    """Monument heritage structural asset model."""

    __tablename__ = "monuments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    location_name = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    heritage_status = Column(String(128), nullable=True)  # e.g. "UNESCO World Heritage Site", "National Monument"
    importance_tier = Column(Integer, default=1, nullable=False)  # 1 (Highest) to 5
    image_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=func.now(), server_default=func.now(), nullable=False)

    # Relationships
    regions = relationship("Region", back_populates="monument", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="monument", cascade="all, delete-orphan")
