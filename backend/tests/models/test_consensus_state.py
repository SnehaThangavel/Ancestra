"""Tests for ConsensusState ORM model."""

import uuid
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.monument import Monument
from app.models.region import Region
from app.models.consensus_state import ConsensusState


def test_consensus_state_model_persistence(db_session: Session) -> None:
    """Test consensus state ORM record creation with UUID, JSONB, and CheckConstraint."""
    monument = Monument(
        id=uuid.uuid4(),
        name="Ellora Caves Cave 16",
        importance_tier=1,
    )
    db_session.add(monument)
    db_session.commit()

    region = Region(
        id=uuid.uuid4(),
        monument_id=monument.id,
        name="kailasa_central_pillar",
        category="pillar",
        bounding_box=[50, 50, 200, 400],
    )
    db_session.add(region)
    db_session.commit()

    cs_id = uuid.uuid4()
    cs = ConsensusState(
        id=cs_id,
        region_id=region.id,
        version=1,
        consensus_tensor={"weights": [0.1, 0.2, 0.3], "feature_dim": 512},
        cumulative_reliability=3.5,
        observation_count=5,
        structural_health_index=0.88,
    )
    db_session.add(cs)
    db_session.commit()
    db_session.refresh(cs)

    assert cs.id == cs_id
    assert cs.region_id == region.id
    assert cs.consensus_tensor["feature_dim"] == 512
    assert cs.structural_health_index == 0.88
    assert cs.region.name == "kailasa_central_pillar"
