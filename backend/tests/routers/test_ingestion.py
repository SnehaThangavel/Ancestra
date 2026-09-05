"""Tests for Ingestion API routes."""

import io
import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_upload_observation_route() -> None:
    """Test /api/v1/ingestion/upload endpoint."""
    # Generate valid test image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    for y in range(480):
        img[y, :, :] = int(120 + 30 * np.sin(y / 20.0))
    cv2.rectangle(img, (100, 100), (300, 400), (40, 40, 40), -1)

    _, encoded = cv2.imencode(".jpg", img)
    img_bytes = io.BytesIO(encoded.tobytes())

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
    assert data["observation_id"] > 0
