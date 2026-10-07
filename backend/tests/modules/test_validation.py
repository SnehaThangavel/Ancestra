"""Comprehensive unit and integration tests for Module 4 (SSIM Anomaly Detection & Validation)."""

import uuid
from datetime import datetime, timezone
import pytest
import numpy as np
import cv2
from sqlalchemy.orm import Session

from app.models.monument import Monument
from app.models.region import Region
from app.models.observation import Observation
from app.models.consensus_state import ConsensusState
from app.models.validation import AnomalyValidation
from app.modules.validation import ValidationModule, get_validation_module
from app.modules.consensus_memory import get_consensus_memory


@pytest.fixture
def validation_module() -> ValidationModule:
    """Fixture providing initialized ValidationModule."""
    return ValidationModule(default_ssim_threshold=0.90)


@pytest.fixture
def sample_monument(db_session: Session) -> Monument:
    """Fixture providing a test monument."""
    mon = Monument(
        id=uuid.uuid4(),
        name="Brihadisvara Temple",
        location_name="Thanjavur",
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
        name="Main_Gopuram_Niche",
        category="carved stone sculpture",
        bounding_box=[50, 50, 300, 300],
    )
    db_session.add(reg)
    db_session.commit()
    db_session.refresh(reg)
    return reg


# -------------------------------------------------------------------------
# 1. Pure SSIM & Bounding Box Extraction Tests
# -------------------------------------------------------------------------
def test_ssim_comparison_identical_images(validation_module: ValidationModule) -> None:
    """Test SSIM comparison on identical pristine images yields no anomalies."""
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.rectangle(img, (50, 50), (250, 250), (180, 180, 180), -1)

    result = validation_module.compute_ssim_comparison(img, img)
    assert result["ssim_score"] >= 0.99
    assert result["ssim_delta"] <= 0.01
    assert result["anomaly_detected"] is False
    assert len(result["defect_bounding_boxes"]) == 0
    assert result["severity_score"] == 0.0


def test_ssim_comparison_defect_detected_with_bounding_boxes(
    validation_module: ValidationModule,
) -> None:
    """Test SSIM comparison on image with structural crack/damage detects defect and extracts bounding box."""
    # Baseline: smooth surface
    baseline = np.full((300, 300, 3), 160, dtype=np.uint8)

    # Query image: injected dark vertical fracture / crack
    query = baseline.copy()
    cv2.rectangle(query, (140, 80), (160, 220), (30, 30, 30), -1)

    result = validation_module.compute_ssim_comparison(query, baseline, ssim_threshold=0.98)

    assert result["ssim_score"] < 0.98
    assert result["ssim_delta"] > 0.02
    assert result["anomaly_detected"] is True
    assert result["severity_score"] > 0.0
    assert len(result["defect_bounding_boxes"]) > 0

    # Verify bounding box bounds the crack location (~150 x)
    bbox = result["defect_bounding_boxes"][0]
    bx, by, bw, bh = bbox
    assert 130 <= bx <= 165
    assert bh > 50  # Tall defect


# -------------------------------------------------------------------------
# 2. Baseline Observation Edge Case Handling
# -------------------------------------------------------------------------
def test_validate_baseline_observation_edge_case(
    validation_module: ValidationModule,
    db_session: Session,
    sample_monument: Monument,
    sample_region: Region,
) -> None:
    """Test analyzing the baseline observation itself returns is_baseline=True with clear message."""
    obs_baseline = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        image_url="uploads/base.jpg",
    )
    db_session.add(obs_baseline)
    db_session.commit()

    # Consensus state pointing to obs_baseline as baseline
    consensus_svc = get_consensus_memory()
    consensus_svc.process_observation(obs_baseline, db=db_session)

    # Validate the baseline observation itself
    response = validation_module.validate_observation(obs_baseline.id, db=db_session)

    assert response.is_baseline is True
    assert response.anomaly_detected is False
    assert response.ssim_score == 1.0
    assert response.severity_score == 0.0
    assert "baseline photo" in response.message.lower()


# -------------------------------------------------------------------------
# 3. End-to-End Anomaly Validation & Structural Health Update
# -------------------------------------------------------------------------
def test_validate_observation_end_to_end(
    validation_module: ValidationModule,
    db_session: Session,
    sample_monument: Monument,
    sample_region: Region,
    tmp_path,
) -> None:
    """Test end-to-end anomaly verification creates AnomalyValidation row and updates ConsensusState health."""
    # 1. Write baseline photo to disk
    base_file = tmp_path / "base.jpg"
    base_img = np.full((300, 300, 3), 150, dtype=np.uint8)
    cv2.imwrite(str(base_file), base_img)

    obs1 = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        image_url=str(base_file),
    )
    db_session.add(obs1)
    db_session.commit()

    consensus_svc = get_consensus_memory()
    consensus_svc.process_observation(obs1, db=db_session)

    # 2. Write second photo with major spalling defect
    defect_file = tmp_path / "defect.jpg"
    defect_img = base_img.copy()
    cv2.circle(defect_img, (150, 150), 50, (30, 30, 30), -1)
    cv2.imwrite(str(defect_file), defect_img)

    obs2 = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        image_url=str(defect_file),
    )
    db_session.add(obs2)
    db_session.commit()
    consensus_svc.process_observation(obs2, db=db_session)

    # 3. Run validation on obs2
    val_resp = validation_module.validate_observation(obs2.id, db=db_session)

    assert val_resp.anomaly_detected is True
    assert val_resp.is_baseline is False
    assert val_resp.ssim_score < 0.95
    assert val_resp.severity_score > 0.10
    assert len(val_resp.defect_bounding_boxes) > 0
    assert val_resp.validation_id is not None

    # 4. Verify AnomalyValidation record in DB
    db_val = db_session.query(AnomalyValidation).filter(AnomalyValidation.id == val_resp.validation_id).first()
    assert db_val is not None
    assert db_val.region_id == sample_region.id
    assert db_val.is_confirmed is True
    assert db_val.observation_id == obs2.id

    # 5. Verify ConsensusState health index updated
    cs = consensus_svc.get_active_consensus_state(sample_region.id, db=db_session)
    assert cs.structural_health_index < 1.0
    assert abs(cs.structural_health_index - (1.0 - val_resp.severity_score)) < 1e-3
