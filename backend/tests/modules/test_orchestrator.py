"""Tests for Module 6 (Orchestrator: Urgency Scoring, Work Order Dispatch & Hash-Chained Evidence Logs)."""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session

from app.models.monument import Monument
from app.models.region import Region
from app.models.consensus_state import ConsensusState
from app.models.validation import AnomalyValidation
from app.models.work_order import WorkOrder, EvidenceLog
from app.modules.orchestrator import OrchestratorModule

SHORE_TEMPLE_MONUMENT_ID = uuid.UUID("3cabc181-8f73-4c35-b3a0-030dd3271f48")
SHORE_TEMPLE_REGION_ID = uuid.UUID("57f11112-75b1-4e1d-80ff-e04f833ccc08")


@pytest.fixture
def seeded_shore_temple_with_defect(db_session: Session) -> Region:
    """Fixture providing Shore Temple region with existing increasing defect validations."""
    monument = Monument(
        id=SHORE_TEMPLE_MONUMENT_ID,
        name="Shore Temple, Mahabalipuram",
        location_name="Mahabalipuram, Tamil Nadu",
        latitude=12.6163,
        longitude=80.1989,
        heritage_status="UNESCO World Heritage Site",
        importance_tier=1,
    )
    db_session.add(monument)

    region = Region(
        id=SHORE_TEMPLE_REGION_ID,
        monument_id=SHORE_TEMPLE_MONUMENT_ID,
        name="East Vimana Plinth",
        category="foundation base",
    )
    db_session.add(region)

    consensus = ConsensusState(
        region_id=SHORE_TEMPLE_REGION_ID,
        version=1,
        structural_health_index=0.35,  # Substantial damage
    )
    db_session.add(consensus)

    t0 = datetime.now(timezone.utc) - timedelta(days=5)
    v1 = AnomalyValidation(
        region_id=SHORE_TEMPLE_REGION_ID,
        anomaly_type="spalling",
        severity_score=0.58,
        created_at=t0,
    )
    v2 = AnomalyValidation(
        region_id=SHORE_TEMPLE_REGION_ID,
        anomaly_type="spalling",
        severity_score=0.65,
        created_at=t0 + timedelta(days=5),
    )
    db_session.add_all([v1, v2])
    db_session.commit()
    return region


def test_compute_urgency_score_critical_shore_temple(
    db_session: Session, seeded_shore_temple_with_defect: Region
) -> None:
    """Test urgency scoring on Shore Temple with high severity (0.65) and increasing degradation."""
    orchestrator = OrchestratorModule()

    urgency = orchestrator.compute_urgency_score(SHORE_TEMPLE_REGION_ID, db=db_session)

    assert urgency["urgency_score"] >= 0.70
    assert urgency["urgency_level"] == "critical"
    assert urgency["severity_score"] == 0.65
    assert urgency["structural_health_index"] == 0.35
    assert urgency["trend_classification"] == "increasing"
    assert "CRITICAL" in urgency["rationale"]


def test_generate_work_order_and_genesis_evidence_block(
    db_session: Session, seeded_shore_temple_with_defect: Region
) -> None:
    """Test generating a work order automatically produces an initial Genesis EvidenceLog block."""
    orchestrator = OrchestratorModule()

    work_order = orchestrator.generate_work_order(
        region_id=SHORE_TEMPLE_REGION_ID,
        db=db_session,
    )

    assert work_order.id is not None
    assert work_order.urgency_index >= 0.70
    assert work_order.status == "pending"
    assert "CRITICAL URGENCY" in work_order.recommended_action

    # Check Genesis block in EvidenceLog
    logs = (
        db_session.query(EvidenceLog)
        .filter(EvidenceLog.work_order_id == work_order.id)
        .all()
    )
    assert len(logs) == 1
    genesis_block = logs[0]
    assert genesis_block.block_index == 0
    assert genesis_block.previous_hash == "0" * 64
    assert len(genesis_block.current_hash) == 64
    assert genesis_block.payload["event_type"] == "work_order_dispatched"


def test_evidence_log_hash_chain_and_tamper_detection(
    db_session: Session, seeded_shore_temple_with_defect: Region
) -> None:
    """Test building a multi-block evidence log chain and detecting unauthorized modifications."""
    orchestrator = OrchestratorModule()

    # 1. Create work order (generates Block #0 Genesis)
    work_order = orchestrator.generate_work_order(
        region_id=SHORE_TEMPLE_REGION_ID,
        db=db_session,
    )

    # 2. Append Block #1: On-site inspection
    b1 = orchestrator.create_evidence_log_entry(
        work_order_id=work_order.id,
        db=db_session,
        event_type="inspection_completed",
        details={"inspector": "Dr. Ramesh (ASI)", "findings": "Micro-cracks propagating along plinth"},
    )
    assert b1.block_index == 1
    assert b1.previous_hash != "0" * 64

    # 3. Append Block #2: Shoring completion
    b2 = orchestrator.create_evidence_log_entry(
        work_order_id=work_order.id,
        db=db_session,
        event_type="shoring_installed",
        details={"contractor": "Heritage Restoration Corp", "props_installed": 4},
    )
    assert b2.block_index == 2
    assert b2.previous_hash == b1.current_hash

    # 4. Verify untampered chain
    verification_clean = orchestrator.verify_evidence_chain(work_order.id, db=db_session)
    assert verification_clean["is_valid"] is True
    assert verification_clean["block_count"] == 3

    # 5. Simulate malicious tampering with Block #1 payload
    b1.payload = {"event_type": "inspection_completed", "tampered_data": True}
    db_session.commit()

    # 6. Verify tampered chain is immediately detected
    verification_tampered = orchestrator.verify_evidence_chain(work_order.id, db=db_session)
    assert verification_tampered["is_valid"] is False
    assert verification_tampered["tampered_block_index"] == 1
    assert "Cryptographic hash corruption" in verification_tampered["error"]
