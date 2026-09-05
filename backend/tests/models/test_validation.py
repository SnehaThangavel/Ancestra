"""Tests for AnomalyValidation ORM model."""

import uuid
import pytest
from sqlalchemy.orm import Session
from app.models.monument import Monument
from app.models.region import Region
from app.models.validation import AnomalyValidation


def test_anomaly_validation_model_persistence(db_session: Session) -> None:
    """Test anomaly validation ORM record creation with UUID, JSONB, and ARRAY(UUID)."""
    monument = Monument(
        id=uuid.uuid4(),
        name="Ajanta Cave 1",
        importance_tier=1,
    )
    db_session.add(monument)
    db_session.commit()

    region = Region(
        id=uuid.uuid4(),
        monument_id=monument.id,
        name="cave1_fresco_wall",
        category="frieze",
    )
    db_session.add(region)
    db_session.commit()

    obs_id1 = uuid.uuid4()
    obs_id2 = uuid.uuid4()
    val_id = uuid.uuid4()

    val = AnomalyValidation(
        id=val_id,
        region_id=region.id,
        anomaly_type="crack",
        ssim_delta=0.22,
        severity_score=0.75,
        corroboration_count=2,
        corroborating_observation_ids=[obs_id1, obs_id2],
        is_confirmed=True,
        defect_polygon={"coordinates": [[10, 10], [20, 25], [15, 30]]},
    )
    db_session.add(val)
    db_session.commit()
    db_session.refresh(val)

    assert val.id == val_id
    assert val.region_id == region.id
    assert val.anomaly_type == "crack"
    assert val.severity_score == 0.75
    assert len(val.corroborating_observation_ids) == 2
    assert val.corroborating_observation_ids[0] == obs_id1
    assert val.defect_polygon["coordinates"][0] == [10, 10]
    assert val.region.name == "cave1_fresco_wall"
