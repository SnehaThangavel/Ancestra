"""Tests for WorkOrder and EvidenceLog ORM models."""

import uuid
import pytest
from sqlalchemy.orm import Session
from app.models.monument import Monument
from app.models.region import Region
from app.models.validation import AnomalyValidation
from app.models.work_order import WorkOrder, EvidenceLog


def test_work_order_and_evidence_log_persistence(db_session: Session) -> None:
    """Test WorkOrder and EvidenceLog ORM models with UUID, JSONB, and hash chaining."""
    monument = Monument(
        id=uuid.uuid4(),
        name="Charminar",
        importance_tier=1,
    )
    db_session.add(monument)
    db_session.commit()

    region = Region(
        id=uuid.uuid4(),
        monument_id=monument.id,
        name="northwest_minaret_base",
        category="pillar",
    )
    db_session.add(region)
    db_session.commit()

    validation = AnomalyValidation(
        id=uuid.uuid4(),
        region_id=region.id,
        anomaly_type="spalling",
        severity_score=0.82,
    )
    db_session.add(validation)
    db_session.commit()

    wo_id = uuid.uuid4()
    work_order = WorkOrder(
        id=wo_id,
        validation_id=validation.id,
        urgency_index=0.85,
        status="pending",
        assigned_team="ASI Conservation Team 4",
        recommended_action="Lime mortar grout injection and surface consolidation",
    )
    db_session.add(work_order)
    db_session.commit()
    db_session.refresh(work_order)

    assert work_order.id == wo_id
    assert work_order.urgency_index == 0.85
    assert work_order.urgency_score == 0.85
    assert work_order.validation.anomaly_type == "spalling"

    # Add hash-chained EvidenceLog entry
    ev_id = uuid.uuid4()
    evidence = EvidenceLog(
        id=ev_id,
        work_order_id=work_order.id,
        block_index=0,
        previous_hash="0000000000000000000000000000000000000000000000000000000000000000",
        current_hash="a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
        payload={"action": "genesis_block", "verified_by": "curator_sys"},
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)

    assert evidence.id == ev_id
    assert evidence.work_order_id == work_order.id
    assert evidence.payload["action"] == "genesis_block"
    assert evidence.work_order.assigned_team == "ASI Conservation Team 4"
