"""Comprehensive tests for Module 2 (Six-Factor Reliability Engine)."""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session
import numpy as np
import cv2

from app.models.observation import Observation
from app.models.monument import Monument
from app.models.region import Region
from app.models.consensus_state import ConsensusState
from app.modules.reliability_engine import ReliabilityEngineModule, get_reliability_engine
from app.modules.ingestion import ImageIngestionModule


@pytest.fixture
def reliability_engine() -> ReliabilityEngineModule:
    """Fixture providing an initialized ReliabilityEngineModule."""
    return ReliabilityEngineModule()


@pytest.fixture
def sample_monument(db_session: Session) -> Monument:
    """Fixture providing a test monument."""
    mon = Monument(
        id=uuid.uuid4(),
        name="Brihadisvara Temple",
        location_name="Thanjavur, Tamil Nadu",
        heritage_status="UNESCO World Heritage",
        importance_tier=1,
    )
    db_session.add(mon)
    db_session.commit()
    db_session.refresh(mon)
    return mon


@pytest.fixture
def sample_region(db_session: Session, sample_monument: Monument) -> Region:
    """Fixture providing a test architectural region."""
    reg = Region(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        name="Vimana_Tower_Base",
        category="masonry wall facade",
        bounding_box=[100, 100, 400, 300],
    )
    db_session.add(reg)
    db_session.commit()
    db_session.refresh(reg)
    return reg


# -------------------------------------------------------------------------
# Factor 1: Image Quality Factor
# -------------------------------------------------------------------------
def test_compute_image_quality_factor(reliability_engine: ReliabilityEngineModule) -> None:
    """Test non-linear quality curve (score ** 1.5)."""
    # High quality (1.0 -> 1.0)
    obs_perfect = {"overall_quality_score": 1.0}
    assert reliability_engine.compute_image_quality_factor(obs_perfect) == 1.0

    # Good quality (0.81 -> 0.81 ** 1.5 = 0.729)
    obs_good = {"overall_quality_score": 0.81}
    score = reliability_engine.compute_image_quality_factor(obs_good)
    assert abs(score - 0.729) < 1e-3

    # Borderline quality (0.49 -> 0.49 ** 1.5 = 0.343)
    obs_border = {"overall_quality_score": 0.49}
    assert reliability_engine.compute_image_quality_factor(obs_border) == 0.343

    # Zero / None handling
    assert reliability_engine.compute_image_quality_factor(None) == 0.0
    assert reliability_engine.compute_image_quality_factor({}) == 0.0


# -------------------------------------------------------------------------
# Factor 2: Geometric Consistency Factor
# -------------------------------------------------------------------------
def test_compute_geometric_consistency_factor(
    reliability_engine: ReliabilityEngineModule,
) -> None:
    """Test geometric consistency with failure floor of 0.1."""
    # Failed registration -> 0.1 floor
    obs_failed = {"registration_success": False, "registration_confidence": 0.0}
    assert reliability_engine.compute_geometric_consistency_factor(obs_failed) == 0.1

    # Missing registration -> 0.1 floor
    assert reliability_engine.compute_geometric_consistency_factor({}) == 0.1
    assert reliability_engine.compute_geometric_consistency_factor(None) == 0.1

    # Successful registration with high confidence
    obs_success = {"registration_success": True, "registration_confidence": 0.85}
    assert reliability_engine.compute_geometric_consistency_factor(obs_success) == 0.85

    # Successful registration with very low confidence -> clamped to 0.1 floor
    obs_low = {"registration_success": True, "registration_confidence": 0.05}
    assert reliability_engine.compute_geometric_consistency_factor(obs_low) == 0.1


# -------------------------------------------------------------------------
# Factor 3: Viewpoint Diversity Factor
# -------------------------------------------------------------------------
def test_compute_viewpoint_diversity_factor_no_prior(
    reliability_engine: ReliabilityEngineModule,
    db_session: Session,
    sample_region: Region,
) -> None:
    """Test viewpoint diversity defaults to 0.5 when no prior observations exist."""
    obs = {"region_id": sample_region.id, "exif_data": {"orientation": 1}}
    assert (
        reliability_engine.compute_viewpoint_diversity_factor(obs, db=db_session)
        == 0.5
    )


def test_compute_viewpoint_diversity_factor_with_history(
    reliability_engine: ReliabilityEngineModule,
    db_session: Session,
    sample_monument: Monument,
    sample_region: Region,
) -> None:
    """Test viewpoint diversity distinguishes duplicates from diverse vantages."""
    now = datetime.now(timezone.utc)

    # Insert 3 prior observations with orientation 1, user A, make Nikon
    for i in range(3):
        prior = Observation(
            monument_id=sample_monument.id,
            region_id=sample_region.id,
            user_id="user_a",
            image_url=f"uploads/p_{i}.jpg",
            overall_quality_score=0.8,
            exif_data={"orientation": 1, "camera_make": "Nikon"},
            created_at=now - timedelta(days=5 + i),
        )
        db_session.add(prior)
    db_session.commit()

    # Query duplicate observation (same user, same orientation, same camera)
    obs_dup = {
        "region_id": sample_region.id,
        "user_id": "user_a",
        "exif_data": {"orientation": 1, "camera_make": "Nikon"},
        "created_at": now,
    }
    dup_score = reliability_engine.compute_viewpoint_diversity_factor(
        obs_dup, db=db_session
    )

    # Query diverse observation (different user, different orientation, different camera)
    obs_diverse = {
        "region_id": sample_region.id,
        "user_id": "user_b",
        "exif_data": {"orientation": 6, "camera_make": "Sony"},
        "created_at": now,
    }
    div_score = reliability_engine.compute_viewpoint_diversity_factor(
        obs_diverse, db=db_session
    )

    assert div_score > dup_score
    assert 0.0 <= dup_score <= 1.0
    assert 0.0 <= div_score <= 1.0


# -------------------------------------------------------------------------
# Factor 4: Temporal Relevance Factor
# -------------------------------------------------------------------------
def test_compute_temporal_relevance_factor(
    reliability_engine: ReliabilityEngineModule,
) -> None:
    """Test exponential decay on age with half-life and non-zero baseline floor."""
    now = datetime.now(timezone.utc)

    # Brand new photo
    obs_new = {"captured_at": now}
    score_new = reliability_engine.compute_temporal_relevance_factor(obs_new)
    assert score_new >= 0.99

    # Photo exactly 1 half-life (180 days) old -> decay is 0.5 -> 0.15 + 0.85*0.5 = 0.575
    obs_half = {"captured_at": now - timedelta(days=180)}
    score_half = reliability_engine.compute_temporal_relevance_factor(obs_half)
    assert abs(score_half - 0.575) < 0.02

    # Very old photo (5 years old) -> should retain non-zero floor (~0.15)
    obs_old = {"captured_at": now - timedelta(days=365 * 5)}
    score_old = reliability_engine.compute_temporal_relevance_factor(obs_old)
    assert score_old >= 0.15
    assert score_old < score_half


# -------------------------------------------------------------------------
# Factor 5: Environmental Similarity Factor
# -------------------------------------------------------------------------
def test_compute_environmental_similarity_factor(
    reliability_engine: ReliabilityEngineModule,
    db_session: Session,
    sample_monument: Monument,
    sample_region: Region,
) -> None:
    """Test lighting similarity against regional history (<3 prior -> 0.5, >=3 -> deviation)."""
    # Case A: < 3 prior observations -> 0.5 default
    obs = {"region_id": sample_region.id, "exposure_score": 0.8}
    assert (
        reliability_engine.compute_environmental_similarity_factor(
            obs, db=db_session
        )
        == 0.5
    )

    # Case B: Insert 3 prior observations with average exposure = 0.80
    for exp in [0.78, 0.80, 0.82]:
        p = Observation(
            monument_id=sample_monument.id,
            region_id=sample_region.id,
            image_url="uploads/test.jpg",
            exposure_score=exp,
            created_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db_session.add(p)
    db_session.commit()

    # Observation with matching exposure (0.80) -> score close to 1.0
    obs_match = {"region_id": sample_region.id, "exposure_score": 0.80}
    score_match = reliability_engine.compute_environmental_similarity_factor(
        obs_match, db=db_session
    )
    assert score_match >= 0.95

    # Observation with wildly deviating exposure (0.20) -> score penalized
    obs_deviant = {"region_id": sample_region.id, "exposure_score": 0.20}
    score_deviant = reliability_engine.compute_environmental_similarity_factor(
        obs_deviant, db=db_session
    )
    assert score_deviant < score_match


# -------------------------------------------------------------------------
# Factor 6: Consensus Agreement Factor
# -------------------------------------------------------------------------
def test_compute_agreement_factor_no_consensus(
    reliability_engine: ReliabilityEngineModule,
    db_session: Session,
    sample_region: Region,
) -> None:
    """Test agreement factor defaults to 1.0 when no consensus state exists."""
    obs = {"region_id": sample_region.id, "overall_quality_score": 0.8}
    assert (
        reliability_engine.compute_agreement_factor(obs, db=db_session) == 1.0
    )


def test_compute_agreement_factor_with_consensus(
    reliability_engine: ReliabilityEngineModule,
    db_session: Session,
    sample_region: Region,
) -> None:
    """Test agreement factor against existing ConsensusState."""
    cs = ConsensusState(
        region_id=sample_region.id,
        version=1,
        structural_health_index=0.9,
        consensus_tensor={"baseline": True},
    )
    db_session.add(cs)
    db_session.commit()

    # Observation with matching quality score
    obs_aligned = {"region_id": sample_region.id, "overall_quality_score": 0.9}
    score_aligned = reliability_engine.compute_agreement_factor(
        obs_aligned, db=db_session
    )
    assert score_aligned == 1.0

    # Observation with mismatching quality score
    obs_mismatch = {"region_id": sample_region.id, "overall_quality_score": 0.4}
    score_mismatch = reliability_engine.compute_agreement_factor(
        obs_mismatch, db=db_session
    )
    assert score_mismatch < 1.0
    assert 0.0 <= score_mismatch <= 1.0


# -------------------------------------------------------------------------
# Composite Reliability & First Observation Edge Case
# -------------------------------------------------------------------------
def test_first_observation_edge_case(
    reliability_engine: ReliabilityEngineModule,
    db_session: Session,
    sample_monument: Monument,
    sample_region: Region,
) -> None:
    """Test scoring the first observation for a region (no prior history, no consensus)."""
    obs = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        user_id="first_contributor",
        image_url="uploads/first_photo.jpg",
        overall_quality_score=0.81,  # f_quality = 0.729
        registration_success=True,
        registration_confidence=0.80,  # f_geom = 0.80
        exposure_score=0.75,  # f_env = 0.5 (default)
        created_at=datetime.now(timezone.utc),  # f_temp = 1.0
        # f_view = 0.5 (default), f_agree = 1.0 (default)
    )
    db_session.add(obs)
    db_session.commit()

    result = reliability_engine.compute_reliability(obs, db=db_session)
    score = result["reliability_score"]
    factors = result["reliability_factors"]

    assert 0.0 <= score <= 1.0
    assert factors["viewpoint_diversity"] == 0.5
    assert factors["environmental_similarity"] == 0.5
    assert factors["agreement"] == 1.0
    assert factors["geometric_consistency"] == 0.8
    assert abs(factors["image_quality"] - 0.729) < 1e-3

    # Check that Observation row was persisted with reliability fields
    db_session.refresh(obs)
    assert obs.reliability_score == score
    assert obs.reliability_factors == factors


def test_custom_weights_and_normalization(
    reliability_engine: ReliabilityEngineModule,
) -> None:
    """Test custom weights combination and automatic normalization."""
    obs = {
        "overall_quality_score": 1.0,  # quality = 1.0
        "registration_success": True,
        "registration_confidence": 1.0,  # geom = 1.0
        "captured_at": datetime.now(timezone.utc),  # temp = 1.0
    }
    # Unnormalized custom weights (all 1.0 -> normalized to 1/6 each)
    custom_w = {
        "image_quality": 2.0,
        "geometric_consistency": 2.0,
        "viewpoint_diversity": 2.0,
        "temporal_relevance": 2.0,
        "environmental_similarity": 2.0,
        "agreement": 2.0,
    }
    res = reliability_engine.compute_reliability(obs, custom_weights=custom_w)
    assert 0.0 <= res["reliability_score"] <= 1.0


# -------------------------------------------------------------------------
# Integration: Ingestion Auto-Scoring Hook
# -------------------------------------------------------------------------
def test_ingestion_module_auto_scores_reliability(
    db_session: Session,
    sample_monument: Monument,
) -> None:
    """Test that ImageIngestionModule automatically computes and populates reliability score."""
    ingestion = ImageIngestionModule(use_ai_segmentation=False)

    # Generate synthetic 600x400 test image bytes
    img = np.zeros((400, 600, 3), dtype=np.uint8)
    cv2.putText(
        img,
        "Temple Pillar",
        (50, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (255, 255, 255),
        3,
    )
    _, encoded = cv2.imencode(".jpg", img)
    image_bytes = encoded.tobytes()

    response = ingestion.ingest(
        image_bytes=image_bytes,
        monument_id=str(sample_monument.id),
        user_id="test_user@heritage.org",
        db=db_session,
        auto_score_reliability=True,
    )

    # Verify that the observation created in DB has reliability_score and reliability_factors populated
    obs = db_session.query(Observation).filter(Observation.id == response.observation_id).first()
    assert obs is not None
    assert obs.reliability_score is not None
    assert 0.0 <= obs.reliability_score <= 1.0
    assert obs.reliability_factors is not None
    assert "image_quality" in obs.reliability_factors
    assert "geometric_consistency" in obs.reliability_factors
    assert "temporal_relevance" in obs.reliability_factors
