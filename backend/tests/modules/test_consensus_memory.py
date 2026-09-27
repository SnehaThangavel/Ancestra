"""Unit and integration tests for Module 3 (Consensus State & Baseline Pointer Manager)."""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

from app.models.monument import Monument
from app.models.region import Region
from app.models.observation import Observation
from app.models.consensus_state import ConsensusState
from app.modules.consensus_memory import ConsensusMemoryModule, get_consensus_memory


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
# 1. Cold-Start Baseline Initialization
# -------------------------------------------------------------------------
def test_cold_start_baseline_initialization(
    consensus_memory: ConsensusMemoryModule,
    db_session: Session,
    sample_monument: Monument,
    sample_region: Region,
) -> None:
    """Test that a region's first observation sets baseline_observation_id and version=1."""
    # Ensure initially no consensus state exists
    assert consensus_memory.get_active_consensus_state(sample_region.id, db=db_session) is None

    # Create first observation
    obs = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        user_id="expert_curator@ancestra.org",
        image_url="uploads/baseline_photo.jpg",
        sharpness_score=0.85,
        exposure_score=0.80,
        overall_quality_score=0.82,
        reliability_score=0.95,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(obs)
    db_session.commit()

    state = consensus_memory.process_observation(obs, db=db_session)
    assert state is not None
    assert state.version == 1
    assert state.region_id == sample_region.id
    assert state.baseline_observation_id == obs.id
    assert state.last_observation_id == obs.id
    assert state.last_updated_by_observation_id == obs.id
    assert state.observation_count == 1
    assert state.structural_health_index == 1.0


# -------------------------------------------------------------------------
# 2. Sequential Observations Update Pointer without Altering Baseline
# -------------------------------------------------------------------------
def test_sequential_observations_update_pointer_without_changing_baseline(
    consensus_memory: ConsensusMemoryModule,
    db_session: Session,
    sample_monument: Monument,
    sample_region: Region,
) -> None:
    """Test subsequent observations update last_observation_id while baseline_observation_id is preserved."""
    # First observation (baseline)
    obs1 = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        image_url="uploads/1.jpg",
    )
    db_session.add(obs1)
    db_session.commit()

    s1 = consensus_memory.process_observation(obs1, db=db_session)
    assert s1.version == 1
    assert s1.baseline_observation_id == obs1.id
    assert s1.last_observation_id == obs1.id
    assert s1.observation_count == 1

    # Second observation
    obs2 = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        image_url="uploads/2.jpg",
    )
    db_session.add(obs2)
    db_session.commit()

    s2 = consensus_memory.process_observation(obs2, db=db_session)
    assert s2.version == 1
    assert s2.baseline_observation_id == obs1.id  # Unchanged baseline
    assert s2.last_observation_id == obs2.id      # Updated pointer
    assert s2.observation_count == 2

    # Third observation
    obs3 = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        image_url="uploads/3.jpg",
    )
    db_session.add(obs3)
    db_session.commit()

    s3 = consensus_memory.process_observation(obs3, db=db_session)
    assert s3.version == 1
    assert s3.baseline_observation_id == obs1.id
    assert s3.last_observation_id == obs3.id
    assert s3.observation_count == 3


# -------------------------------------------------------------------------
# 3. Explicit Restoration Baseline Reset
# -------------------------------------------------------------------------
def test_explicit_restoration_baseline_reset(
    consensus_memory: ConsensusMemoryModule,
    db_session: Session,
    sample_monument: Monument,
    sample_region: Region,
) -> None:
    """Test triggering a restoration reset creates a new version and updates baseline pointer."""
    # Initial baseline
    obs1 = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        image_url="uploads/obs1.jpg",
    )
    db_session.add(obs1)
    db_session.commit()
    consensus_memory.process_observation(obs1, db=db_session)

    # Trigger restoration reset with new baseline photo
    obs_repair = Observation(
        id=uuid.uuid4(),
        monument_id=sample_monument.id,
        region_id=sample_region.id,
        image_url="uploads/post_repair.jpg",
    )
    db_session.add(obs_repair)
    db_session.commit()

    reset_state = consensus_memory.reset_baseline(
        region_id=sample_region.id,
        reason="Masonry pointing and crack injection completed",
        baseline_observation_id=obs_repair.id,
        db=db_session,
    )

    assert reset_state.version == 2
    assert reset_state.baseline_observation_id == obs_repair.id
    assert reset_state.last_observation_id == obs_repair.id
    assert reset_state.reset_reason == "Masonry pointing and crack injection completed"
    assert reset_state.structural_health_index == 1.0

    # Verify history has 2 records
    history = consensus_memory.get_consensus_history(sample_region.id, db=db_session)
    assert len(history) == 2
    assert history[0].version == 1
    assert history[0].baseline_observation_id == obs1.id
    assert history[1].version == 2
    assert history[1].baseline_observation_id == obs_repair.id
