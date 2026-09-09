"""Tests for Reliability API routes (Module 2)."""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.monument import Monument
from app.models.region import Region
from app.models.observation import Observation


def test_score_observation_route_success(
    client: TestClient,
    db_session: Session,
) -> None:
    """Test POST /api/v1/reliability/score/{observation_id} endpoint successfully."""
    # 1. Create Monument and Region
    mon = Monument(
        id=uuid.uuid4(),
        name="Sun Temple",
        location_name="Konark, Odisha",
        heritage_status="UNESCO World Heritage",
        importance_tier=1,
    )
    db_session.add(mon)
    db_session.commit()

    reg = Region(
        id=uuid.uuid4(),
        monument_id=mon.id,
        name="Chariot_Wheel_East",
        category="carved stone sculpture",
        bounding_box=[50, 50, 200, 200],
    )
    db_session.add(reg)
    db_session.commit()

    # 2. Create Observation
    obs = Observation(
        id=uuid.uuid4(),
        monument_id=mon.id,
        region_id=reg.id,
        user_id="curator@ancestra.org",
        image_url="uploads/sun_wheel.jpg",
        overall_quality_score=0.88,
        sharpness_score=0.90,
        exposure_score=0.85,
        registration_success=True,
        registration_confidence=0.80,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(obs)
    db_session.commit()

    # 3. Call endpoint
    response = client.post(f"/api/v1/reliability/score/{obs.id}")
    assert response.status_code == 200

    data = response.json()
    assert str(data["observation_id"]) == str(obs.id)
    assert "reliability_score" in data
    assert 0.0 <= data["reliability_score"] <= 1.0
    assert "factors" in data
    factors = data["factors"]
    assert "image_quality" in factors
    assert "geometric_consistency" in factors
    assert "viewpoint_diversity" in factors
    assert "temporal_relevance" in factors
    assert "environmental_similarity" in factors
    assert "agreement" in factors


def test_score_observation_not_found(client: TestClient) -> None:
    """Test POST /api/v1/reliability/score/{observation_id} with non-existent UUID returns 404."""
    random_id = uuid.uuid4()
    response = client.post(f"/api/v1/reliability/score/{random_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_score_observation_invalid_uuid(client: TestClient) -> None:
    """Test POST /api/v1/reliability/score/{observation_id} with invalid format returns 400."""
    response = client.post("/api/v1/reliability/score/not-a-valid-uuid")
    assert response.status_code == 400
    assert "invalid observation uuid" in response.json()["detail"].lower()
