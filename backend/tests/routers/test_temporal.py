"""Tests for Temporal Evolution API routes."""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.monument import Monument
from app.models.region import Region
from app.models.consensus_state import ConsensusState
from app.models.validation import AnomalyValidation

SHORE_TEMPLE_MONUMENT_ID = uuid.UUID("3cabc181-8f73-4c35-b3a0-030dd3271f48")
SHORE_TEMPLE_REGION_ID = uuid.UUID("57f11112-75b1-4e1d-80ff-e04f833ccc08")


def test_get_deterioration_trend_route(client: TestClient, db_session: Session) -> None:
    """Test /api/v1/temporal/trend endpoint for Shore Temple."""
    # Seed Shore Temple monument and region
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
        structural_health_index=0.95,
    )
    db_session.add(consensus)

    # Add 2 anomalies
    t0 = datetime.now(timezone.utc) - timedelta(days=10)
    v1 = AnomalyValidation(
        region_id=SHORE_TEMPLE_REGION_ID,
        anomaly_type="crack",
        severity_score=0.10,
        created_at=t0,
    )
    v2 = AnomalyValidation(
        region_id=SHORE_TEMPLE_REGION_ID,
        anomaly_type="crack",
        severity_score=0.25,
        created_at=t0 + timedelta(days=10),
    )
    db_session.add_all([v1, v2])
    db_session.commit()

    # Call /api/v1/temporal/trend
    payload = {
        "region_id": str(SHORE_TEMPLE_REGION_ID),
        "forecast_days": 90,
    }
    response = client.post("/api/v1/temporal/trend", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["region_id"] == str(SHORE_TEMPLE_REGION_ID)
    assert data["status"] == "calculated"
    assert data["trend_classification"] == "increasing"
    assert data["is_projection_estimate"] is True
    assert data["projected_health_index_90d"] <= 0.95
