"""Tests for Monument ORM model."""

import uuid
import pytest
from sqlalchemy.orm import Session
from app.models.monument import Monument


def test_monument_model_persistence(db_session: Session) -> None:
    """Test Monument ORM record creation and database persistence."""
    mon_id = uuid.uuid4()
    monument = Monument(
        id=mon_id,
        name="Brihadeeswarar Temple",
        location_name="Thanjavur, Tamil Nadu",
        latitude=10.7828,
        longitude=79.1318,
        heritage_status="UNESCO World Heritage Site",
        importance_tier=1,
    )
    db_session.add(monument)
    db_session.commit()
    db_session.refresh(monument)

    assert monument.id == mon_id
    assert monument.name == "Brihadeeswarar Temple"
    assert monument.importance_tier == 1
    assert monument.created_at is not None
    assert monument.updated_at is not None
