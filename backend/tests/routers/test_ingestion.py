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


def test_upload_with_explicit_region_id_route(client: TestClient) -> None:
    """Test /api/v1/ingestion/upload endpoint with explicit expert region_id."""
    img_bytes = _make_test_image_bytes()
    explicit_region_id = str(uuid.uuid4())

    response = client.post(
        "/api/v1/ingestion/upload",
        data={
            "monument_id": "TAJ_MAHAL_001",
            "region_id": explicit_region_id,
            "user_id": "expert_conservator_01",
        },
        files={"file": ("monument.jpg", img_bytes, "image/jpeg")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["matched_region_id"] == explicit_region_id
    assert data["is_baseline"] is True  # First upload for this region ID is cold start baseline
    assert data["registration_success"] is True
