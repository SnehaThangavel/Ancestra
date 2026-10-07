"""Tests for Consensus API routes (Module 3)."""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.monument import Monument
from app.models.region import Region
from app.models.observation import Observation
from app.models.consensus_state import ConsensusState


def test_get_region_consensus_success_and_not_found(
    client: TestClient,
    db_session: Session,
) -> None:
    """Test GET /api/v1/consensus/{region_id} returns 200 when state exists and 404 when absent."""
    mon = Monument(
        id=uuid.uuid4(),
        name="Meenakshi Temple",
        location_name="Madurai",
        heritage_status="National Monument",
        importance_tier=1,
    )
    db_session.add(mon)
    db_session.commit()

    reg = Region(
        id=uuid.uuid4(),
        monument_id=mon.id,
        name="South_Tower_Pillar",
        category="stone pillar column",
    )
    db_session.add(reg)
    db_session.commit()

    # 1. Check 404 before state exists
    resp_404 = client.get(f"/api/v1/consensus/{reg.id}")
    assert resp_404.status_code == 404

    # 2. Add Observation and ConsensusState
    obs = Observation(
        id=uuid.uuid4(),
        monument_id=mon.id,
        region_id=reg.id,
        user_id="test_user@heritage.org",
        image_url="test_photo.jpg",
        blur_score=120.0,
        glare_score=0.05,
        is_valid_quality=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(obs)
    db_session.commit()

    cs = ConsensusState(
        id=uuid.uuid4(),
        region_id=reg.id,
        version=1,
        baseline_observation_id=obs.id,
        last_updated_by_observation_id=obs.id,
        observation_count=1,
        structural_health_index=1.0,
    )
    db_session.add(cs)
    db_session.commit()

    # 3. Check 200 OK after state exists
    resp_200 = client.get(f"/api/v1/consensus/{reg.id}")
    assert resp_200.status_code == 200
    data = resp_200.json()
    assert data["region_id"] == str(reg.id)
    assert data["version"] == 1
    assert data["baseline_observation_id"] == str(obs.id)
    assert data["last_observation_id"] == str(obs.id)
    assert data["structural_health_index"] == 1.0


def test_record_observation_pointer_endpoint(
    client: TestClient,
    db_session: Session,
) -> None:
    """Test POST /api/v1/consensus/record-observation updates pointer."""
    mon = Monument(
        id=uuid.uuid4(),
        name="Shore Temple",
        location_name="Mahabalipuram",
        heritage_status="UNESCO",
        importance_tier=1,
    )
    db_session.add(mon)
    db_session.commit()

    reg = Region(
        id=uuid.uuid4(),
        monument_id=mon.id,
        name="East_Sanctuary_Wall",
        category="masonry wall facade",
    )
    db_session.add(reg)
    db_session.commit()

    obs = Observation(
        id=uuid.uuid4(),
        monument_id=mon.id,
        region_id=reg.id,
        image_url="uploads/shore.jpg",
        overall_quality_score=0.9,
    )
    db_session.add(obs)
    db_session.commit()

    # Call record-observation
    resp = client.post(
        "/api/v1/consensus/record-observation",
        json={"observation_id": str(obs.id), "region_id": str(reg.id)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["region_id"] == str(reg.id)
    assert data["baseline_observation_id"] == str(obs.id)
    assert data["last_observation_id"] == str(obs.id)
    assert data["observation_count"] == 1


def test_reset_region_baseline_endpoint(
    client: TestClient,
    db_session: Session,
) -> None:
    """Test POST /api/v1/consensus/{region_id}/reset-baseline creates a new version."""
    mon = Monument(
        id=uuid.uuid4(),
        name="Sun Temple",
        location_name="Konark",
        heritage_status="UNESCO",
        importance_tier=1,
    )
    db_session.add(mon)
    db_session.commit()

    reg = Region(
        id=uuid.uuid4(),
        monument_id=mon.id,
        name="Wheel_Section_1",
        category="stone relief",
    )
    db_session.add(reg)
    db_session.commit()

    obs = Observation(
        id=uuid.uuid4(),
        monument_id=mon.id,
        region_id=reg.id,
        image_url="uploads/konark.jpg",
    )
    db_session.add(obs)
    db_session.commit()

    # First initialize v1
    client.post(
        "/api/v1/consensus/record-observation",
        json={"observation_id": str(obs.id), "region_id": str(reg.id)},
    )

    # Now trigger restoration reset
    resp_reset = client.post(
        f"/api/v1/consensus/{reg.id}/reset-baseline",
        json={
            "reason": "Complete chemical cleaning and stone consolidation",
            "baseline_observation_id": str(obs.id),
        },
    )
    assert resp_reset.status_code == 200
    data = resp_reset.json()
    assert data["version"] == 2
    assert data["reset_reason"] == "Complete chemical cleaning and stone consolidation"
    assert data["baseline_observation_id"] == str(obs.id)

    # Check history endpoint
    resp_hist = client.get(f"/api/v1/consensus/{reg.id}/history")
    assert resp_hist.status_code == 200
    hist_data = resp_hist.json()
    assert len(hist_data) == 2
    assert hist_data[0]["version"] == 1
    assert hist_data[1]["version"] == 2
