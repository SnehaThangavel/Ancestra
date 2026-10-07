"""Tests for Validation Pydantic schemas (Module 4)."""

import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas.validation import AnomalyValidationRequest, AnomalyValidationResponse


def test_validation_schemas_valid() -> None:
    """Test valid instantiation of validation schemas."""
    obs_id = uuid.uuid4()
    reg_id = uuid.uuid4()

    req = AnomalyValidationRequest(
        observation_id=obs_id,
        region_id=reg_id,
        ssim_threshold=0.88,
    )
    assert req.observation_id == obs_id
    assert req.region_id == reg_id
    assert req.ssim_threshold == 0.88

    resp = AnomalyValidationResponse(
        validation_id=uuid.uuid4(),
        observation_id=obs_id,
        region_id=reg_id,
        anomaly_detected=True,
        anomaly_type="crack",
        ssim_score=0.78,
        ssim_delta=0.22,
        severity_score=0.35,
        defect_bounding_boxes=[[10, 20, 30, 40]],
        corroboration_count=1,
        is_confirmed=True,
        is_baseline=False,
    )
    assert resp.anomaly_detected is True
    assert resp.anomaly_type == "crack"
    assert resp.defect_bounding_boxes == [[10, 20, 30, 40]]


def test_validation_schemas_invalid_threshold() -> None:
    """Test out of bounds ssim_threshold validation."""
    with pytest.raises(ValidationError):
        AnomalyValidationRequest(
            observation_id=uuid.uuid4(),
            ssim_threshold=1.5,  # > 1.0
        )
