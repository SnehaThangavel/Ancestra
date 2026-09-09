"""Tests for Consensus Pydantic schemas (SESCI Module 3)."""

import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas.consensus import (
    ConsensusUpdateRequest,
    ConsensusResetRequest,
    ConsensusStateResponse,
)


def test_consensus_schemas_valid() -> None:
    """Test valid instantiation and serialization of consensus schemas."""
    obs_id = uuid.uuid4()
    reg_id = uuid.uuid4()

    # Update request
    up_req = ConsensusUpdateRequest(
        observation_id=obs_id,
        region_id=reg_id,
        reliability_weight=0.85,
    )
    assert up_req.observation_id == obs_id
    assert up_req.reliability_weight == 0.85

    # Reset request
    res_req = ConsensusResetRequest(reason="Post-restoration recalibration")
    assert res_req.reason == "Post-restoration recalibration"

    # Response schema
    now = datetime.now(timezone.utc)
    resp = ConsensusStateResponse(
        id=uuid.uuid4(),
        region_id=reg_id,
        version=1,
        structural_health_index=0.92,
        cumulative_reliability=3.45,
        observation_count=4,
        consensus_tensor={"histogram": [0.03] * 32, "mean_intensity": 140.0},
        last_updated_by_observation_id=obs_id,
        reset_reason=None,
        created_at=now,
        updated_at=now,
    )
    assert resp.region_id == reg_id
    assert resp.version == 1
    assert resp.structural_health_index == 0.92
    assert resp.cumulative_reliability == 3.45
    assert resp.observation_count == 4
    assert resp.last_updated == now
    assert resp.state_vector_summary == resp.consensus_tensor


def test_consensus_schemas_out_of_bounds() -> None:
    """Test validation errors on out-of-bound structural health index and weights."""
    with pytest.raises(ValidationError):
        ConsensusStateResponse(
            region_id=uuid.uuid4(),
            version=1,
            structural_health_index=1.5,  # > 1.0
            cumulative_reliability=1.0,
            observation_count=1,
        )

    with pytest.raises(ValidationError):
        ConsensusUpdateRequest(
            observation_id=uuid.uuid4(),
            reliability_weight=-0.5,  # < 0.0
        )
