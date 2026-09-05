"""Tests for Region ORM model."""

import uuid
import pytest
from sqlalchemy.orm import Session
from app.models.monument import Monument
from app.models.region import Region


def test_region_model_persistence(db_session: Session) -> None:
    """Test region ORM record creation with UUID and JSONB bounding box."""
    monument = Monument(
        id=uuid.uuid4(),
        name="Konark Sun Temple",
        location_name="Konark, Odisha",
        importance_tier=1,
    )
    db_session.add(monument)
    db_session.commit()

    reg_id = uuid.uuid4()
    region = Region(
        id=reg_id,
        monument_id=monument.id,
        name="chariot_wheel_01",
        category="carved stone sculpture",
        bounding_box=[100, 150, 200, 200],
        reference_features={"keypoints": 128, "embedding_dim": 512},
    )
    db_session.add(region)
    db_session.commit()
    db_session.refresh(region)

    assert region.id == reg_id
    assert region.monument_id == monument.id
    assert region.bounding_box == [100, 150, 200, 200]
    assert region.reference_features["keypoints"] == 128
    assert region.monument.name == "Konark Sun Temple"
