"""Tests for Validation API routes (Module 4)."""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.monument import Monument
from app.models.region import Region
from app.models.observation import Observation
from app.models.consensus_state import ConsensusState
from app.models.validation import AnomalyValidation
from app.modules.consensus_memory import get_consensus_memory


def test_verify_anomaly_endpoint(
    client: TestClient,
    db_session: Session,
    tmp_path,
) -> None:
    """Test POST /api/v1/validation/verify endpoint."""
    import cv2
    import numpy as np

    mon = Monument(
        id=uuid.uuid4(),
        name="Brihadisvara Temple",
        location_name="Thanjavur",
        heritage_status="UNESCO",
        importance_tier=1,
    )
    db_session.add(mon)
    db_session.commit()

    reg = Region(
        id=uuid.uuid4(),
        monument_id=mon.id,
        name="Main_Wall",
        category="facade",
    )
    db_session.add(reg)
    db_session.commit()

    # Baseline observation
    base_file = tmp_path / "base.jpg"
    base_img = np.full((300, 300, 3), 150, dtype=np.uint8)
    cv2.imwrite(str(base_file), base_img)

    obs1 = Observation(
        id=uuid.uuid4(),
        monument_id=mon.id,
        region_id=reg.id,
        image_url=str(base_file),
    )
    db_session.add(obs1)
    db_session.commit()

    # Initialize consensus v1
    consensus_svc = get_consensus_memory()
    consensus_svc.process_observation(obs1, db=db_session)

    # 1. Verify baseline returns is_baseline=True
    resp_base = client.post(
        "/api/v1/validation/verify",
        json={"observation_id": str(obs1.id), "region_id": str(reg.id)},
    )
    assert resp_base.status_code == 200
    data_base = resp_base.json()
    assert data_base["is_baseline"] is True
    assert data_base["anomaly_detected"] is False

    # 2. Second observation
    defect_file = tmp_path / "obs2.jpg"
    defect_img = base_img.copy()
    cv2.rectangle(defect_img, (50, 50), (150, 150), (20, 20, 20), -1)
    cv2.imwrite(str(defect_file), defect_img)

    obs2 = Observation(
        id=uuid.uuid4(),
        monument_id=mon.id,
        region_id=reg.id,
        image_url=str(defect_file),
    )
    db_session.add(obs2)
    db_session.commit()
    consensus_svc.process_observation(obs2, db=db_session)

    resp_obs2 = client.post(
        "/api/v1/validation/verify",
        json={"observation_id": str(obs2.id), "region_id": str(reg.id)},
    )
    assert resp_obs2.status_code == 200
    data_obs2 = resp_obs2.json()
    assert data_obs2["is_baseline"] is False
    assert "severity_score" in data_obs2
    assert "defect_bounding_boxes" in data_obs2


def test_list_region_anomalies_endpoint(
    client: TestClient,
    db_session: Session,
) -> None:
    """Test GET /api/v1/validation/region/{region_id} endpoint."""
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
        name="East_Pillar",
        category="pillar",
    )
    db_session.add(reg)
    db_session.commit()

    obs_id = uuid.uuid4()
    val = AnomalyValidation(
        id=uuid.uuid4(),
        region_id=reg.id,
        anomaly_type="crack",
        ssim_delta=0.25,
        severity_score=0.45,
        corroboration_count=1,
        corroborating_observation_ids=[obs_id],
        is_confirmed=True,
        defect_polygon={"bounding_boxes": [[10, 20, 30, 40]]},
    )
    db_session.add(val)
    db_session.commit()

    resp = client.get(f"/api/v1/validation/region/{reg.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["anomaly_type"] == "crack"
    assert data[0]["severity_score"] == 0.45
    assert data[0]["defect_bounding_boxes"] == [[10, 20, 30, 40]]


def test_get_observation_anomaly_endpoint(
    client: TestClient,
    db_session: Session,
) -> None:
    """Test GET /api/v1/validation/observation/{observation_id} endpoint."""
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
        name="Wheel_Base",
        category="relief",
    )
    db_session.add(reg)
    db_session.commit()

    obs_id = uuid.uuid4()
    val = AnomalyValidation(
        id=uuid.uuid4(),
        region_id=reg.id,
        anomaly_type="spalling",
        ssim_delta=0.35,
        severity_score=0.60,
        corroboration_count=1,
        corroborating_observation_ids=[obs_id],
        is_confirmed=True,
        defect_polygon={"bounding_boxes": [[50, 60, 70, 80]]},
    )
    db_session.add(val)
    db_session.commit()

    resp = client.get(f"/api/v1/validation/observation/{obs_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["observation_id"] == str(obs_id)
    assert data["anomaly_type"] == "spalling"
    assert data["severity_score"] == 0.60
