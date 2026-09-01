"""Tests for Ingestion API routes."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_upload_observation_route() -> None:
    """Test /api/v1/ingestion/upload endpoint."""
    pass
