"""Tests for Orchestrator API routes."""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.monument import Monument
from app.models.region import Region
from app.models.consensus_state import ConsensusState
from app.models.validation import AnomalyValidation
from app.models.work_order import WorkOrder

SHORE_TEMPLE_MONUMENT_ID = uuid.UUID("3cabc181-8f73-4c35-b3a0-030dd3271f48")
SHORE_TEMPLE_REGION_ID = uuid.UUID("57f11112-75b1-4e1d-80ff-e04f833ccc08")


@pytest.fixture
def seeded_shore_temple_route(db_session: Session) -> Region:
    """Fixture providing Shore Temple region with validations for route testing."""
    monument = Monument(
        id=SHORE_TEMPLE_MONUMENT_ID,
        name="Shore Temple, Mahabalipuram",
        location_name="Mahabalipuram, Tamil Nadu",
        latitude=12.6163,
        longitude=80.1989,
        heritage_status="UNESCO World Heritage Site",
        importance_tier=1,
    )
    db_session.add(monument)

    region = Region(
        id=SHORE_TEMPLE_REGION_ID,
        monument_id=SHORE_TEMPLE_MONUMENT_ID,
        name="East Vimana Plinth",
        category="foundation base",
    )
    db_session.add(region)

    consensus = ConsensusState(
        region_id=SHORE_TEMPLE_REGION_ID,
        version=1,
        structural_health_index=0.40,
    )
    db_session.add(consensus)

    val = AnomalyValidation(
        region_id=SHORE_TEMPLE_REGION_ID,
        anomaly_type="spalling",
        severity_score=0.62,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(val)
    db_session.commit()
    return region


def test_get_region_urgency_endpoint(client: TestClient, seeded_shore_temple_route: Region) -> None:
    """Test GET /api/v1/orchestrator/urgency/{region_id}."""
    resp = client.get(f"/api/v1/orchestrator/urgency/{SHORE_TEMPLE_REGION_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["region_id"] == str(SHORE_TEMPLE_REGION_ID)
    assert data["urgency_score"] >= 0.45
    assert data["urgency_level"] in ["high", "critical"]


def test_create_and_list_work_orders_endpoint(client: TestClient, seeded_shore_temple_route: Region) -> None:
    """Test POST /api/v1/orchestrator/work-orders and GET /api/v1/orchestrator/work-orders."""
    # 1. Create work order
    create_payload = {
        "region_id": str(SHORE_TEMPLE_REGION_ID),
        "assigned_team": "ASI Southern Circle Conservation Team",
    }
    create_resp = client.post("/api/v1/orchestrator/work-orders", json=create_payload)
    assert create_resp.status_code == 201
    wo_data = create_resp.json()
    assert wo_data["assigned_team"] == "ASI Southern Circle Conservation Team"
    wo_id = wo_data["id"]

    # 2. List work orders
    list_resp = client.get("/api/v1/orchestrator/work-orders")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert any(item["id"] == wo_id for item in list_data)

    # 3. Retrieve evidence logs for work order
    evidence_resp = client.get(f"/api/v1/orchestrator/work-orders/{wo_id}/evidence")
    assert evidence_resp.status_code == 200
    evidence_data = evidence_resp.json()
    assert len(evidence_data) >= 1
    assert evidence_data[0]["block_index"] == 0

    # 4. Verify chain integrity endpoint
    verify_resp = client.get(f"/api/v1/orchestrator/work-orders/{wo_id}/verify-chain")
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["is_valid"] is True
    assert verify_data["block_count"] >= 1
