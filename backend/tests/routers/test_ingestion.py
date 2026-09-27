"""Tests for Ingestion API routes."""

import io
import uuid
import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient


def _make_test_image_bytes(width=640, height=480) -> io.BytesIO:
    """Helper to create dummy JPEG test bytes."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        img[y, :, :] = int(120 + 30 * np.sin(y / 20.0))
    cv2.rectangle(img, (100, 100), (300, 400), (40, 40, 40), -1)
    _, encoded = cv2.imencode(".jpg", img)
    return io.BytesIO(encoded.tobytes())


def test_upload_observation_route(client: TestClient) -> None:
    """Test /api/v1/ingestion/upload endpoint."""
    img_bytes = _make_test_image_bytes()

    response = client.post(
        "/api/v1/ingestion/upload",
        data={"monument_id": "TAJ_MAHAL_001", "user_id": "test_user"},
        files={"file": ("monument.jpg", img_bytes, "image/jpeg")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["monument_id"] == "TAJ_MAHAL_001"
    assert data["resolution_w"] == 640
    assert data["resolution_h"] == 480
    assert data["observation_id"] is not None
    assert uuid.UUID(str(data["observation_id"]))


def test_suggest_region_route(client: TestClient) -> None:
    """Test /api/v1/ingestion/suggest-region endpoint."""
    img_bytes = _make_test_image_bytes()

    response = client.post(
        "/api/v1/ingestion/suggest-region",
        data={"monument_id": "TAJ_MAHAL_001"},
        files={"file": ("monument.jpg", img_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["monument_id"] == "TAJ_MAHAL_001"
    assert "suggested_region_id" in data
    assert "confidence_score" in data
    assert "available_regions" in data
    assert isinstance(data["available_regions"], list)


def test_upload_with_explicit_region_id_route(client: TestClient, db_session) -> None:
    """Test /api/v1/ingestion/upload endpoint with explicit expert region_id automatically updates consensus_state."""
    from app.models.consensus_state import ConsensusState

    img_bytes = _make_test_image_bytes()
    explicit_region_id = str(uuid.uuid4())

    # 1. First upload (cold-start baseline)
    response = client.post(
        "/api/v1/ingestion/upload",
        data={
            "monument_id": "TAJ_MAHAL_001",
            "region_id": explicit_region_id,
            "user_id": "expert_conservator_01",
        },
        files={"file": ("monument_1.jpg", img_bytes, "image/jpeg")},
    )

    assert response.status_code == 201
    data = response.json()
    obs1_id = uuid.UUID(data["observation_id"])
    assert data["matched_region_id"] == explicit_region_id
    assert data["is_baseline"] is True
    assert data["registration_success"] is True

    # Verify consensus_states row was automatically initialized for this region
    cs = db_session.query(ConsensusState).filter(ConsensusState.region_id == uuid.UUID(explicit_region_id)).first()
    assert cs is not None
    assert cs.version == 1
    assert cs.baseline_observation_id == obs1_id
    assert cs.last_observation_id == obs1_id
    assert cs.observation_count == 1

    # 2. Second upload for the same region
    img_bytes2 = _make_test_image_bytes()
    response2 = client.post(
        "/api/v1/ingestion/upload",
        data={
            "monument_id": "TAJ_MAHAL_001",
            "region_id": explicit_region_id,
            "user_id": "expert_conservator_01",
        },
        files={"file": ("monument_2.jpg", img_bytes2, "image/jpeg")},
    )
    assert response2.status_code == 201
    obs2_id = uuid.UUID(response2.json()["observation_id"])

    # Verify consensus_states pointer updated automatically without changing baseline
    db_session.refresh(cs)
    assert cs.version == 1
    assert cs.baseline_observation_id == obs1_id
    assert cs.last_observation_id == obs2_id
    assert cs.observation_count == 2

