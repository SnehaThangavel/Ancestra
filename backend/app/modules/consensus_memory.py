"""Module 3: Regional Consensus State & Baseline Pointer Manager.

SESCI Architecture - Module 3 (Baseline State & Restoration Pointer Management):
Maintains the active baseline observation and latest observation pointer for each
architectural region. Handles deliberate post-restoration baseline version resets
for physical repair events without Bayesian tensor blending.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Union, List, Any
from sqlalchemy.orm import Session

from app.models.consensus_state import ConsensusState
from app.models.observation import Observation
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ConsensusMemoryModule:
    """Module 3 implementation: Regional baseline state and observation pointer manager."""

    def __init__(self) -> None:
        """Initialize Module 3 service."""
        pass

    # -------------------------------------------------------------------------
    # 1. Query Active State & History
    # -------------------------------------------------------------------------
    def get_active_consensus_state(
        self, region_id: Union[uuid.UUID, str], db: Session
    ) -> Optional[ConsensusState]:
        """Fetch the current active ConsensusState for a region (highest version number).

        Args:
            region_id: Region UUID or identifier.
            db: SQLAlchemy database session.

        Returns:
            Optional[ConsensusState]: Active ConsensusState or None if cold-start.
        """
        region_uuid = self._resolve_uuid(region_id)
        return (
            db.query(ConsensusState)
            .filter(ConsensusState.region_id == region_uuid)
            .order_by(ConsensusState.version.desc())
            .first()
        )

    def get_consensus_history(
        self, region_id: Union[uuid.UUID, str], db: Session
    ) -> List[ConsensusState]:
        """Fetch all historical consensus state versions for a region.

        Args:
            region_id: Region UUID or identifier.
            db: SQLAlchemy database session.

        Returns:
            List[ConsensusState]: Chronological list of consensus states by version.
        """
        region_uuid = self._resolve_uuid(region_id)
        return (
            db.query(ConsensusState)
            .filter(ConsensusState.region_id == region_uuid)
            .order_by(ConsensusState.version.asc())
            .all()
        )

    # -------------------------------------------------------------------------
    # 2. Initialize Baseline Pointer (Cold Start)
    # -------------------------------------------------------------------------
    def initialize_consensus_state(
        self,
        region_id: Union[uuid.UUID, str],
        observation: Observation,
        db: Session,
        **kwargs: Any,
    ) -> ConsensusState:
        """Initialize version 1 ConsensusState establishing baseline and last observation pointers.

        Args:
            region_id: Region UUID or identifier.
            observation: First observation record serving as initial baseline.
            db: SQLAlchemy database session.

        Returns:
            ConsensusState: Newly initialized version 1 ConsensusState.
        """
        region_uuid = self._resolve_uuid(region_id)
        obs_id = getattr(observation, "id", None)

        new_state = ConsensusState(
            region_id=region_uuid,
            version=1,
            baseline_observation_id=obs_id,
            last_updated_by_observation_id=obs_id,
            observation_count=1,
            structural_health_index=1.0,  # Default initial health condition
            reset_reason="Initial baseline photo",
            cumulative_reliability=1.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(new_state)
        db.commit()
        db.refresh(new_state)
        logger.info(
            f"Initialized version 1 ConsensusState for Region ID {region_uuid} "
            f"(baseline_obs={obs_id})"
        )
        return new_state

    # -------------------------------------------------------------------------
    # 3. Update Latest Observation Pointer
    # -------------------------------------------------------------------------
    def update_consensus_state(
        self,
        region_id: Union[uuid.UUID, str],
        observation: Observation,
        db: Session,
        **kwargs: Any,
    ) -> ConsensusState:
        """Update last_observation pointer on the active ConsensusState without altering baseline.

        Args:
            region_id: Region UUID or identifier.
            observation: New confirmed expert observation.
            db: SQLAlchemy database session.

        Returns:
            ConsensusState: Updated active ConsensusState record.
        """
        region_uuid = self._resolve_uuid(region_id)
        active_state = self.get_active_consensus_state(region_uuid, db)

        if active_state is None:
            return self.initialize_consensus_state(region_uuid, observation, db)

        obs_id = getattr(observation, "id", None)

        # If baseline pointer was unset (e.g., after a reset awaiting first photo)
        if active_state.baseline_observation_id is None and obs_id is not None:
            active_state.baseline_observation_id = obs_id

        active_state.last_updated_by_observation_id = obs_id
        active_state.observation_count = int(active_state.observation_count or 0) + 1
        active_state.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(active_state)
        logger.info(
            f"Updated ConsensusState v{active_state.version} for Region ID {region_uuid} "
            f"(last_obs={obs_id}, count={active_state.observation_count})"
        )
        return active_state

    # -------------------------------------------------------------------------
    # 4. Explicit Restoration / Repair Baseline Reset
    # -------------------------------------------------------------------------
    def reset_baseline(
        self,
        region_id: Union[uuid.UUID, str],
        reason: Optional[str],
        db: Session,
        baseline_observation_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> ConsensusState:
        """Create a new incremented ConsensusState version following verified physical restoration.

        Preserves previous versions in history while establishing a new baseline reference point.

        Args:
            region_id: Region UUID or identifier.
            reason: Explanation of the restoration/repair action.
            db: SQLAlchemy database session.
            baseline_observation_id: Optional specific observation ID to serve as new baseline.

        Returns:
            ConsensusState: Newly created incremented version ConsensusState.
        """
        region_uuid = self._resolve_uuid(region_id)
        latest_state = self.get_active_consensus_state(region_uuid, db)
        next_version = (latest_state.version + 1) if latest_state else 1

        resolved_base_obs = (
            self._resolve_uuid(baseline_observation_id)
            if baseline_observation_id is not None
            else None
        )

        new_version_state = ConsensusState(
            region_id=region_uuid,
            version=next_version,
            baseline_observation_id=resolved_base_obs,
            last_updated_by_observation_id=resolved_base_obs,
            observation_count=1 if resolved_base_obs is not None else 0,
            structural_health_index=1.0,  # Post-repair baseline reset to pristine state
            reset_reason=reason or "Post-restoration baseline reset",
            cumulative_reliability=1.0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(new_version_state)
        db.commit()
        db.refresh(new_version_state)
        logger.info(
            f"Created new ConsensusState version {next_version} for Region ID {region_uuid} "
            f"(reason='{reason}', baseline_obs={resolved_base_obs})"
        )
        return new_version_state

    def create_new_consensus_version(
        self,
        region_id: Union[uuid.UUID, str],
        reason: Optional[str],
        db: Session,
        baseline_observation_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> ConsensusState:
        """Alias for reset_baseline for backward compatibility."""
        return self.reset_baseline(
            region_id=region_id,
            reason=reason,
            db=db,
            baseline_observation_id=baseline_observation_id,
        )

    # -------------------------------------------------------------------------
    # 5. Unified Entry Point
    # -------------------------------------------------------------------------
    def process_observation(
        self,
        observation: Observation,
        db: Session,
        **kwargs: Any,
    ) -> Optional[ConsensusState]:
        """Incorporate observation into regional consensus state by updating pointer.

        Args:
            observation: Observation record.
            db: SQLAlchemy database session.

        Returns:
            Optional[ConsensusState]: Active or updated ConsensusState record.
        """
        if observation is None or observation.region_id is None:
            logger.warning("Observation has no associated region_id; skipping consensus update.")
            return None

        active_state = self.get_active_consensus_state(observation.region_id, db)
        if active_state is None:
            return self.initialize_consensus_state(
                region_id=observation.region_id,
                observation=observation,
                db=db,
            )

        return self.update_consensus_state(
            region_id=observation.region_id,
            observation=observation,
            db=db,
        )

    # -------------------------------------------------------------------------
    # Helper Utilities
    # -------------------------------------------------------------------------
    @staticmethod
    def _resolve_uuid(id_val: Union[uuid.UUID, str]) -> uuid.UUID:
        """Safely convert identifier to UUID object."""
        if isinstance(id_val, uuid.UUID):
            return id_val
        try:
            return uuid.UUID(str(id_val))
        except (ValueError, AttributeError):
            return uuid.uuid5(uuid.NAMESPACE_DNS, str(id_val))


def get_consensus_memory() -> ConsensusMemoryModule:
    """Factory function providing a configured ConsensusMemoryModule instance."""
    return ConsensusMemoryModule()
