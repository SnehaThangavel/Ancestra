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
    )
    assert up_req.observation_id == obs_id
    assert up_req.region_id == reg_id

    # Reset request
    res_req = ConsensusResetRequest(
        reason="Post-restoration recalibration",
        baseline_observation_id=obs_id,
    )
    assert res_req.reason == "Post-restoration recalibration"
    assert res_req.baseline_observation_id == obs_id

    # Response schema
    now = datetime.now(timezone.utc)
    resp = ConsensusStateResponse(
        id=uuid.uuid4(),
        region_id=reg_id,
        version=1,
        baseline_observation_id=obs_id,
        last_observation_id=obs_id,
        structural_health_index=0.92,
        observation_count=4,
        reset_reason=None,
        created_at=now,
        updated_at=now,
    )
    assert resp.region_id == reg_id
    assert resp.version == 1
    assert resp.baseline_observation_id == obs_id
    assert resp.last_observation_id == obs_id
    assert resp.structural_health_index == 0.92
    assert resp.observation_count == 4
    assert resp.last_updated == now


def test_consensus_schemas_out_of_bounds() -> None:
    """Test validation errors on out-of-bound structural health index."""
    with pytest.raises(ValidationError):
        ConsensusStateResponse(
            region_id=uuid.uuid4(),
            version=1,
            structural_health_index=1.5,  # > 1.0
            observation_count=1,
        )
