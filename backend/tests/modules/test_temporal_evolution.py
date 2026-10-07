"""Tests for Module 5 (Temporal Deterioration Trend Forecasting & Confidence Labeling)."""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session

from app.models.monument import Monument
from app.models.region import Region
from app.models.consensus_state import ConsensusState
from app.models.validation import AnomalyValidation
from app.modules.consensus_memory import ConsensusMemoryModule
from app.modules.temporal_evolution import TemporalEvolutionModule

# Real seeded Shore Temple region UUID as specified
SHORE_TEMPLE_MONUMENT_ID = uuid.UUID("3cabc181-8f73-4c35-b3a0-030dd3271f48")
SHORE_TEMPLE_REGION_ID = uuid.UUID("57f11112-75b1-4e1d-80ff-e04f833ccc08")


@pytest.fixture
def seeded_shore_temple_region(db_session: Session) -> Region:
    """Fixture to ensure the real Shore Temple monument and region exist in the test DB."""
    monument = db_session.query(Monument).filter(Monument.id == SHORE_TEMPLE_MONUMENT_ID).first()
    if not monument:
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
        db_session.flush()

    region = db_session.query(Region).filter(Region.id == SHORE_TEMPLE_REGION_ID).first()
    if not region:
        region = Region(
            id=SHORE_TEMPLE_REGION_ID,
            monument_id=monument.id,
            name="East Vimana Plinth",
            category="foundation base",
            bounding_box={"x": 120, "y": 450, "width": 480, "height": 220},
        )
        db_session.add(region)
        db_session.flush()

    consensus = (
        db_session.query(ConsensusState)
        .filter(ConsensusState.region_id == SHORE_TEMPLE_REGION_ID)
        .first()
    )
    if not consensus:
        consensus = ConsensusState(
            region_id=region.id,
            version=1,
            structural_health_index=1.0,
            cumulative_reliability=1.0,
            observation_count=0,
            created_at=datetime.now(timezone.utc) - timedelta(days=60),
            updated_at=datetime.now(timezone.utc) - timedelta(days=60),
        )
        db_session.add(consensus)
        db_session.flush()

    db_session.commit()
    return region


def test_estimate_deterioration_rate_insufficient_data(
    db_session: Session, seeded_shore_temple_region: Region
) -> None:
    """Test that fewer than 2 AnomalyValidation records returns status='insufficient_data'."""
    temporal_mod = TemporalEvolutionModule()

    # Case 0: No validation records
    result = temporal_mod.estimate_deterioration_rate(SHORE_TEMPLE_REGION_ID, db=db_session)
    assert result["status"] == "insufficient_data"
    assert result["record_count"] == 0
    assert result["projection_confidence"] == "low"

    # Case 1: Exactly 1 validation record
    single_val = AnomalyValidation(
        region_id=SHORE_TEMPLE_REGION_ID,
        anomaly_type="crack",
        ssim_delta=0.12,
        severity_score=0.18,
        corroboration_count=1,
        is_confirmed=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(single_val)
    db_session.commit()

    result_single = temporal_mod.estimate_deterioration_rate(SHORE_TEMPLE_REGION_ID, db=db_session)
    assert result_single["status"] == "insufficient_data"
    assert result_single["record_count"] == 1


def test_estimate_deterioration_rate_increasing_trend_and_confidence(
    db_session: Session, seeded_shore_temple_region: Region
) -> None:
    """Test computing deterioration rate on multiple anomaly validations with increasing severity and confidence grading."""
    temporal_mod = TemporalEvolutionModule()
    t0 = datetime.now(timezone.utc) - timedelta(days=3)

    # 2 sparse records over 3 days -> confidence should be 'low'
    val1 = AnomalyValidation(
        region_id=SHORE_TEMPLE_REGION_ID,
        anomaly_type="masonry_crack",
        ssim_delta=0.08,
        severity_score=0.10,
        is_confirmed=True,
        created_at=t0,
    )
    val2 = AnomalyValidation(
        region_id=SHORE_TEMPLE_REGION_ID,
        anomaly_type="masonry_crack",
        ssim_delta=0.18,
        severity_score=0.22,
        is_confirmed=True,
        created_at=t0 + timedelta(days=3),
    )
    db_session.add_all([val1, val2])
    db_session.commit()

    res = temporal_mod.estimate_deterioration_rate(SHORE_TEMPLE_REGION_ID, db=db_session)
    assert res["status"] == "calculated"
    assert res["record_count"] == 2
    assert res["trend_classification"] == "increasing"
    assert res["deterioration_rate_per_day"] > 0
    assert res["projection_confidence"] == "low"
    assert "limited data" in res["confidence_note"]


def test_confidence_improves_with_time_and_records(
    db_session: Session, seeded_shore_temple_region: Region
) -> None:
    """Test that confidence transitions from low -> medium -> high as dataset expands."""
    temporal_mod = TemporalEvolutionModule()
    t0 = datetime.now(timezone.utc) - timedelta(days=120)

    # Seed 12 records spanning 120 days
    vals = []
    for i in range(12):
        vals.append(
            AnomalyValidation(
                region_id=SHORE_TEMPLE_REGION_ID,
                anomaly_type="spalling",
                ssim_delta=0.05 + (i * 0.02),
                severity_score=0.10 + (i * 0.03),
                is_confirmed=True,
                created_at=t0 + timedelta(days=i * 10),
            )
        )
    db_session.add_all(vals)
    db_session.commit()

    res = temporal_mod.estimate_deterioration_rate(SHORE_TEMPLE_REGION_ID, db=db_session)
    assert res["status"] == "calculated"
    assert res["record_count"] == 12
    assert res["projection_confidence"] == "high"


def test_project_future_health_and_critical_horizon(
    db_session: Session, seeded_shore_temple_region: Region
) -> None:
    """Test structural health linear projection and critical threshold estimation."""
    temporal_mod = TemporalEvolutionModule(critical_health_threshold=0.40)
    t0 = datetime.now(timezone.utc) - timedelta(days=20)

    val1 = AnomalyValidation(
        region_id=SHORE_TEMPLE_REGION_ID,
        anomaly_type="crack",
        ssim_delta=0.10,
        severity_score=0.15,
        created_at=t0,
    )
    val2 = AnomalyValidation(
        region_id=SHORE_TEMPLE_REGION_ID,
        anomaly_type="crack",
        ssim_delta=0.25,
        severity_score=0.35,
        created_at=t0 + timedelta(days=20),
    )
    db_session.add_all([val1, val2])
    db_session.commit()

    proj = temporal_mod.project_future_health(
        region_id=SHORE_TEMPLE_REGION_ID,
        db=db_session,
        horizon_days=90,
        critical_threshold=0.40,
    )

    assert proj["is_projection_estimate"] is True
    assert "Linear forecast estimate" in proj["projection_label"]
    assert proj["projection_confidence"] == "low"
    assert proj["current_health_index"] == 1.0
    assert proj["projected_health_index"] < 1.0
    assert proj["trend_classification"] == "increasing"
    assert proj["time_to_critical_threshold_days"] is not None
    assert proj["time_to_critical_threshold_days"] > 0


def test_restoration_reset_resets_trend_window(
    db_session: Session, seeded_shore_temple_region: Region
) -> None:
    """Test that a restoration baseline reset (ConsensusState version bump) resets the trend window."""
    temporal_mod = TemporalEvolutionModule()
    consensus_mod = ConsensusMemoryModule()

    # Pre-restoration records
    old_time = datetime.now(timezone.utc) - timedelta(days=50)
    old_val1 = AnomalyValidation(
        region_id=SHORE_TEMPLE_REGION_ID,
        anomaly_type="severe_spalling",
        severity_score=0.60,
        created_at=old_time,
    )
    old_val2 = AnomalyValidation(
        region_id=SHORE_TEMPLE_REGION_ID,
        anomaly_type="severe_spalling",
        severity_score=0.75,
        created_at=old_time + timedelta(days=10),
    )
    db_session.add_all([old_val1, old_val2])
    db_session.commit()

    # Verify trend is calculated before restoration
    res_before = temporal_mod.estimate_deterioration_rate(SHORE_TEMPLE_REGION_ID, db=db_session)
    assert res_before["status"] == "calculated"
    assert res_before["active_restoration_version"] == 1

    # Execute Module 3 restoration reset (version bump to v2)
    new_state = consensus_mod.reset_baseline(
        region_id=SHORE_TEMPLE_REGION_ID,
        reason="Structural grouting and basalt stabilization completed",
        db=db_session,
    )
    assert new_state.version == 2

    # Immediately after restoration, historical window resets -> insufficient data
    res_after_reset = temporal_mod.estimate_deterioration_rate(SHORE_TEMPLE_REGION_ID, db=db_session)
    assert res_after_reset["status"] == "insufficient_data"
    assert res_after_reset["active_restoration_version"] == 2
    assert res_after_reset["record_count"] == 0

    # Add 2 new post-restoration monitoring records
    post_time = datetime.now(timezone.utc)
    new_val1 = AnomalyValidation(
        region_id=SHORE_TEMPLE_REGION_ID,
        anomaly_type="minor_efflorescence",
        severity_score=0.08,
        created_at=post_time,
    )
    new_val2 = AnomalyValidation(
        region_id=SHORE_TEMPLE_REGION_ID,
        anomaly_type="minor_efflorescence",
        severity_score=0.09,
        created_at=post_time + timedelta(days=5),
    )
    db_session.add_all([new_val1, new_val2])
    db_session.commit()

    # Now trend window computes exclusively across the new restoration epoch
    res_post_monitoring = temporal_mod.estimate_deterioration_rate(SHORE_TEMPLE_REGION_ID, db=db_session)
    assert res_post_monitoring["status"] == "calculated"
    assert res_post_monitoring["record_count"] == 2
    assert res_post_monitoring["active_restoration_version"] == 2
    assert res_post_monitoring["severity_start"] == 0.08
    assert res_post_monitoring["severity_current"] == 0.09
