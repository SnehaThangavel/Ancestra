"""Tests for Observation ORM model."""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session
from app.models.monument import Monument
from app.models.observation import Observation


def test_observation_model_persistence(db_session: Session) -> None:
    """Test observation ORM record creation with UUID, JSONB, and Monument relationship."""
    monument = Monument(
        id=uuid.uuid4(),
        name="Hampi Virupaksha Temple",
        location_name="Hampi, Karnataka",
        importance_tier=1,
    )
    db_session.add(monument)
    db_session.commit()

    obs_id = uuid.uuid4()
    obs = Observation(
        id=obs_id,
        monument_id=monument.id,
        user_id="curator_101",
        image_url="uploads/hampi_pillar.jpg",
        captured_at=datetime.now(timezone.utc),
        blur_score=0.92,
        sharpness_score=0.92,
        glare_score=0.04,
        exposure_score=0.96,
        overall_quality_score=0.91,
        is_valid_quality=True,
        resolution_width=1920,
        resolution_height=1080,
        exif_data={"camera": "Sony A7III", "iso": 100, "focal_length": 35.0},
        registration_success=True,
        registration_confidence=0.88,
        reliability_score=0.90,
        reliability_factors={"sensor_quality": 0.95, "lighting_condition": 0.88},
    )
    db_session.add(obs)
    db_session.commit()
    db_session.refresh(obs)

    assert obs.id == obs_id
    assert obs.monument_id == monument.id
    assert obs.exif_data["camera"] == "Sony A7III"
    assert obs.reliability_factors["sensor_quality"] == 0.95
    assert obs.is_valid_quality is True
    assert obs.monument.name == "Hampi Virupaksha Temple"
