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

    # 2. Add ConsensusState
    cs = ConsensusState(
        id=uuid.uuid4(),
        region_id=reg.id,
        version=1,
        cumulative_reliability=2.5,
        observation_count=3,
        structural_health_index=0.95,
        consensus_tensor={"histogram": [0.03] * 32, "mean_intensity": 130.0},
    )
    db_session.add(cs)
    db_session.commit()

    # 3. Check 200 OK after state exists
    resp_200 = client.get(f"/api/v1/consensus/{reg.id}")
    assert resp_200.status_code == 200
    data = resp_200.json()
    assert data["region_id"] == str(reg.id)
    assert data["version"] == 1
    assert data["structural_health_index"] == 0.95
    assert data["cumulative_reliability"] == 2.5
    assert data["observation_count"] == 3


def test_update_region_consensus_endpoint(
    client: TestClient,
    db_session: Session,
) -> None:
    """Test POST /api/v1/consensus/update manually triggers consensus update."""
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
        reliability_score=0.88,
    )
    db_session.add(obs)
    db_session.commit()

    # Trigger update
    payload = {
        "observation_id": str(obs.id),
        "region_id": str(reg.id),
        "reliability_weight": 0.88,
    }
    response = client.post("/api/v1/consensus/update", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["region_id"] == str(reg.id)
    assert data["version"] == 1
    assert data["observation_count"] == 1
    assert data["cumulative_reliability"] == 0.88


def test_reset_region_consensus_endpoint(
    client: TestClient,
    db_session: Session,
) -> None:
    """Test POST /api/v1/consensus/{region_id}/reset creates incremented consensus version."""
    mon = Monument(
        id=uuid.uuid4(),
        name="Golconda Fort",
        location_name="Hyderabad",
        heritage_status="Heritage Site",
        importance_tier=2,
    )
    db_session.add(mon)
    db_session.commit()

    reg = Region(
        id=uuid.uuid4(),
        monument_id=mon.id,
        name="Acoustic_Dome_Ceiling",
        category="structural dome roof",
    )
    db_session.add(reg)
    db_session.commit()

    # Initial state v1
    cs_v1 = ConsensusState(
        id=uuid.uuid4(),
        region_id=reg.id,
        version=1,
        cumulative_reliability=4.0,
        observation_count=5,
        structural_health_index=0.80,
    )
    db_session.add(cs_v1)
    db_session.commit()

    # Call reset endpoint
    reset_payload = {"reason": "Completed dome waterproofing and structural underpinning"}
    response = client.post(f"/api/v1/consensus/{reg.id}/reset", json=reset_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 2
    assert data["observation_count"] == 0
    assert data["cumulative_reliability"] == 0.0
    assert data["reset_reason"] == "Completed dome waterproofing and structural underpinning"
