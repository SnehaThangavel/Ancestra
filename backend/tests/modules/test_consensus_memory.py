"""Comprehensive unit and integration tests for Module 3 (Consensus Memory Module)."""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session
import numpy as np
import cv2

from app.models.monument import Monument
from app.models.region import Region
from app.models.observation import Observation
from app.models.consensus_state import ConsensusState
from app.modules.consensus_memory import ConsensusMemoryModule, get_consensus_memory
from app.modules.ingestion import ImageIngestionModule


@pytest.fixture
def consensus_memory() -> ConsensusMemoryModule:
    """Fixture providing initialized ConsensusMemoryModule."""
    return ConsensusMemoryModule()


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
        name="Main_Gopuram_Niche",
        category="carved stone sculpture",
        bounding_box=[50, 50, 300, 300],
    )
    db_session.add(reg)
    db_session.commit()
    db_session.refresh(reg)
    return reg


# -------------------------------------------------------------------------
# 1. Cold-Start Initialization
# -------------------------------------------------------------------------
def test_cold_start_initialization(
    consensus_memory: ConsensusMemoryModule,
    db_session: Session,
    sample_monument: Monument,
    sample_region: Region,
) -> None:
    """Test that a region's first-ever observation creates version 1 ConsensusState."""
    # Ensure initially no consensus state exists
    assert consensus_memory.get_active_consensus_state(sample_region.id, db=db_session) is None

    # Create first observation
    obs = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        user_id="archaeologist@ancestra.org",
        image_url="uploads/photo1.jpg",
        sharpness_score=0.85,
        exposure_score=0.80,
        overall_quality_score=0.82,
        reliability_score=0.80,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(obs)
    db_session.commit()

    # Synthetic image array for test
    img = np.full((100, 100, 3), 150, dtype=np.uint8)

    state = consensus_memory.process_observation(obs, db=db_session, image=img)
    assert state is not None
    assert state.version == 1
    assert state.region_id == sample_region.id
    assert state.cumulative_reliability == 0.80
    assert state.observation_count == 1
    assert state.structural_health_index == 1.0  # Assumed healthy at cold start
    assert state.last_updated_by_observation_id == obs.id
    assert state.consensus_tensor is not None
    assert "histogram" in state.consensus_tensor
    assert "mean_intensity" in state.consensus_tensor
    assert len(state.consensus_tensor["histogram"]) == 32


# -------------------------------------------------------------------------
# 2. Reliability-Weighted Running Update Math
# -------------------------------------------------------------------------
def test_weighted_running_update_math(
    consensus_memory: ConsensusMemoryModule,
    db_session: Session,
    sample_monument: Monument,
    sample_region: Region,
) -> None:
    """Verify that low-reliability observations shift consensus tensor less than high-reliability ones."""
    # 1. Initialize state with baseline mean_intensity = 100.0, reliability = 1.0
    initial_tensor = {
        "histogram": [round(1.0 / 32, 5)] * 32,
        "mean_intensity": 100.0,
        "std_intensity": 20.0,
        "laplacian_variance": 50.0,
        "channels_mean": [100.0, 100.0, 100.0],
    }
    state = ConsensusState(
        id=uuid.uuid4(),
        region_id=sample_region.id,
        version=1,
        cumulative_reliability=1.0,
        observation_count=1,
        structural_health_index=1.0,
        consensus_tensor=initial_tensor,
    )
    db_session.add(state)
    db_session.commit()

    # Create image with mean intensity = 200.0
    bright_img = np.full((100, 100, 3), 200, dtype=np.uint8)

    # 2. Case A: Low-reliability observation (reliability = 0.10)
    obs_low = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        reliability_score=0.10,
        image_url="uploads/low.jpg",
    )
    db_session.add(obs_low)
    db_session.commit()

    updated_low = consensus_memory.update_consensus_state(
        sample_region.id, obs_low, db=db_session, image=bright_img
    )
    # Expected mean = (100.0 * 1.0 + 200.0 * 0.1) / 1.1 = 120.0 / 1.1 = 109.09
    mean_low = updated_low.consensus_tensor["mean_intensity"]
    assert abs(mean_low - 109.09) < 0.5
    assert updated_low.cumulative_reliability == 1.10
    assert updated_low.observation_count == 2

    # 3. Case B: Another Region with High-reliability observation (reliability = 1.0)
    reg_b = Region(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        name="Region_B",
        category="masonry wall facade",
    )
    db_session.add(reg_b)
    db_session.commit()

    state_b = ConsensusState(
        id=uuid.uuid4(),
        region_id=reg_b.id,
        version=1,
        cumulative_reliability=1.0,
        observation_count=1,
        structural_health_index=1.0,
        consensus_tensor=initial_tensor,
    )
    db_session.add(state_b)
    db_session.commit()

    obs_high = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=reg_b.id,
        reliability_score=1.0,
        image_url="uploads/high.jpg",
    )
    db_session.add(obs_high)
    db_session.commit()

    updated_high = consensus_memory.update_consensus_state(
        reg_b.id, obs_high, db=db_session, image=bright_img
    )
    # Expected mean = (100.0 * 1.0 + 200.0 * 1.0) / 2.0 = 150.00
    mean_high = updated_high.consensus_tensor["mean_intensity"]
    assert abs(mean_high - 150.00) < 0.5

    # Low reliability shifted the mean by ~9, while high reliability shifted by ~50
    shift_low = abs(mean_low - 100.0)
    shift_high = abs(mean_high - 100.0)
    assert shift_high > (shift_low * 4.0)


# -------------------------------------------------------------------------
# 3. Observation Count & Health Preservation
# -------------------------------------------------------------------------
def test_multiple_sequential_updates(
    consensus_memory: ConsensusMemoryModule,
    db_session: Session,
    sample_monument: Monument,
    sample_region: Region,
) -> None:
    """Test sequential updates increment observation_count and cumulative_reliability without changing structural_health_index."""
    img = np.full((100, 100, 3), 120, dtype=np.uint8)

    # First observation
    obs1 = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        reliability_score=0.8,
        image_url="uploads/1.jpg",
    )
    db_session.add(obs1)
    db_session.commit()
    s1 = consensus_memory.process_observation(obs1, db=db_session, image=img)
    assert s1.observation_count == 1
    assert s1.cumulative_reliability == 0.8
    assert s1.structural_health_index == 1.0

    # Second observation
    obs2 = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        reliability_score=0.7,
        image_url="uploads/2.jpg",
    )
    db_session.add(obs2)
    db_session.commit()
    s2 = consensus_memory.process_observation(obs2, db=db_session, image=img)
    assert s2.observation_count == 2
    assert abs(s2.cumulative_reliability - 1.5) < 1e-3
    assert s2.structural_health_index == 1.0
    assert s2.last_updated_by_observation_id == obs2.id


# -------------------------------------------------------------------------
# 4. Versioning & Reset Mechanism
# -------------------------------------------------------------------------
def test_create_new_consensus_version(
    consensus_memory: ConsensusMemoryModule,
    db_session: Session,
    sample_monument: Monument,
    sample_region: Region,
) -> None:
    """Test that explicit reset creates version 2 while preserving version 1 in history."""
    # 1. Initialize version 1 with 2 observations
    img = np.full((100, 100, 3), 130, dtype=np.uint8)
    obs1 = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        reliability_score=0.9,
        image_url="uploads/v1.jpg",
    )
    db_session.add(obs1)
    db_session.commit()
    consensus_memory.process_observation(obs1, db=db_session, image=img)

    # 2. Trigger version reset
    reason_text = "Laser stone surface cleaning and mortar grouting completed"
    v2_state = consensus_memory.create_new_consensus_version(
        region_id=sample_region.id,
        reason=reason_text,
        db=db_session,
    )

    assert v2_state.version == 2
    assert v2_state.observation_count == 0
    assert v2_state.cumulative_reliability == 0.0
    assert v2_state.consensus_tensor is None
    assert v2_state.reset_reason == reason_text
    assert v2_state.structural_health_index == 1.0

    # 3. Verify that version 1 STILL EXISTS in database history
    all_states = (
        db_session.query(ConsensusState)
        .filter(ConsensusState.region_id == sample_region.id)
        .order_by(ConsensusState.version.asc())
        .all()
    )
    assert len(all_states) == 2
    assert all_states[0].version == 1
    assert all_states[0].observation_count == 1
    assert all_states[1].version == 2
    assert all_states[1].observation_count == 0

    # 4. Verify that get_active_consensus_state returns version 2
    active = consensus_memory.get_active_consensus_state(sample_region.id, db=db_session)
    assert active.version == 2

    # 5. Verify that the next incoming observation populates version 2 fresh
    obs_new = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        reliability_score=0.85,
        image_url="uploads/v2_first.jpg",
    )
    db_session.add(obs_new)
    db_session.commit()

    updated_v2 = consensus_memory.process_observation(obs_new, db=db_session, image=img)
    assert updated_v2.version == 2
    assert updated_v2.observation_count == 1
    assert updated_v2.cumulative_reliability == 0.85
    assert updated_v2.consensus_tensor is not None


# -------------------------------------------------------------------------
# 5. Integration: Ingestion Pipeline Auto-Update Hook
# -------------------------------------------------------------------------
def test_ingestion_module_auto_updates_consensus(
    db_session: Session,
    sample_monument: Monument,
) -> None:
    """Test that ImageIngestionModule automatically creates/updates ConsensusState on photo upload."""
    ingestion = ImageIngestionModule(use_ai_segmentation=False)

    # Generate synthetic 600x400 test image bytes
    img = np.zeros((400, 600, 3), dtype=np.uint8)
    cv2.rectangle(img, (100, 100), (500, 300), (180, 180, 180), -1)
    _, encoded = cv2.imencode(".jpg", img)
    image_bytes = encoded.tobytes()

    response = ingestion.ingest(
        image_bytes=image_bytes,
        monument_id=str(sample_monument.id),
        user_id="curator@ancestra.org",
        db=db_session,
    )

    assert response.matched_region_id is not None

    # Verify that ConsensusState exists and was updated automatically
    consensus_state = (
        db_session.query(ConsensusState)
        .filter(ConsensusState.region_id == response.matched_region_id)
        .first()
    )
    assert consensus_state is not None
    assert consensus_state.version == 1
    assert consensus_state.observation_count >= 1
    assert consensus_state.cumulative_reliability > 0.0
    assert consensus_state.consensus_tensor is not None


def test_process_observation_sequential_regression(
    consensus_memory: ConsensusMemoryModule,
    db_session: Session,
    sample_monument: Monument,
    sample_region: Region,
) -> None:
    """Regression test: Calling process_observation() twice for the same region updates state instead of reinitializing."""
    img = np.full((100, 100, 3), 140, dtype=np.uint8)

    # First observation
    obs1 = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        user_id="user1@ancestra.org",
        image_url="uploads/photo1.jpg",
        reliability_score=0.7474,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(obs1)
    db_session.commit()

    state1 = consensus_memory.process_observation(obs1, db=db_session, image=img)
    assert state1 is not None
    assert state1.observation_count == 1
    assert abs(state1.cumulative_reliability - 0.7474) < 1e-4
    assert state1.last_updated_by_observation_id == obs1.id

    # Second observation on the SAME region
    obs2 = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        user_id="user2@ancestra.org",
        image_url="uploads/photo2.jpg",
        reliability_score=0.8200,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(obs2)
    db_session.commit()

    state2 = consensus_memory.process_observation(obs2, db=db_session, image=img)
    assert state2 is not None
    # Must be 2 (updated in-place), not reset to 1
    assert state2.observation_count == 2
    # Must be sum of both reliabilities: 0.7474 + 0.8200 = 1.5674
    assert abs(state2.cumulative_reliability - 1.5674) < 1e-3
    assert state2.last_updated_by_observation_id == obs2.id

    # Query DB fresh to confirm persistence
    db_state = (
        db_session.query(ConsensusState)
        .filter(ConsensusState.region_id == sample_region.id)
        .first()
    )
    assert db_state is not None
    assert db_state.observation_count == 2
    assert abs(db_state.cumulative_reliability - 1.5674) < 1e-3
    assert db_state.last_updated_by_observation_id == obs2.id


def test_ingestion_module_sequential_uploads_accumulate_consensus(
    db_session: Session,
    sample_monument: Monument,
) -> None:
    """Test that uploading two photos to the same monument/region increments observation_count to 2."""
    ingestion = ImageIngestionModule(use_ai_segmentation=False)

    img = np.zeros((400, 600, 3), dtype=np.uint8)
    cv2.rectangle(img, (100, 100), (500, 300), (180, 180, 180), -1)
    _, encoded = cv2.imencode(".jpg", img)
    image_bytes = encoded.tobytes()

    # Upload 1
    res1 = ingestion.ingest(
        image_bytes=image_bytes,
        monument_id=str(sample_monument.id),
        user_id="user1@ancestra.org",
        db=db_session,
    )
    assert res1.matched_region_id is not None
    region_id = res1.matched_region_id

    state1 = (
        db_session.query(ConsensusState)
        .filter(ConsensusState.region_id == region_id)
        .first()
    )
    assert state1 is not None
    assert state1.observation_count == 1
    rel1 = state1.cumulative_reliability

    # Upload 2 (same photo / region)
    res2 = ingestion.ingest(
        image_bytes=image_bytes,
        monument_id=str(sample_monument.id),
        user_id="user2@ancestra.org",
        db=db_session,
    )
    assert res2.matched_region_id == region_id

    # Re-query ConsensusState
    db_session.expire_all()
    state2 = (
        db_session.query(ConsensusState)
        .filter(ConsensusState.region_id == region_id)
        .first()
    )
    assert state2 is not None
    assert state2.observation_count == 2
    assert state2.cumulative_reliability > rel1

