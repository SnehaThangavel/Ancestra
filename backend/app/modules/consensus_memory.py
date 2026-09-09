"""Module 3: Reliability-Weighted Continuous Running Consensus Memory Update.

SESCI Architecture - Patent Claim Scope:
Maintains a running, incrementally-updated baseline condition representation (ConsensusState)
for each architectural region, weighted by each observation's reliability score from Module 2.

Reliability-Adaptive Evidence Fusion:
    new_tensor = (old_tensor * cumulative_reliability + new_obs_tensor * obs.reliability_score) /
                 (cumulative_reliability + obs.reliability_score)
    cumulative_reliability += obs.reliability_score
    observation_count += 1
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import numpy as np
import cv2
from sqlalchemy.orm import Session

from app.models.consensus_state import ConsensusState
from app.models.observation import Observation
from app.utils.image_utils import load_image_cv2, compute_laplacian_variance
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ConsensusMemoryModule:
    """Production-grade implementation of Module 3: Consensus Memory State Management."""

    def __init__(self, alpha_decay: float = 0.95) -> None:
        """Initialize consensus memory module parameters.

        Args:
            alpha_decay: Optional temporal decay parameter for historical consensus tensor memory.
        """
        self.alpha_decay = alpha_decay

    # -------------------------------------------------------------------------
    # 1. Active Consensus State Query
    # -------------------------------------------------------------------------
    def get_active_consensus_state(
        self, region_id: Union[uuid.UUID, str], db: Session
    ) -> Optional[ConsensusState]:
        """Fetch the latest active ConsensusState for a region (highest version number).

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

    # -------------------------------------------------------------------------
    # 2. Feature Representation Extraction Helper
    # -------------------------------------------------------------------------
    def _compute_feature_representation(
        self, image: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Compute statistical visual feature representation tensor for an observation crop.

        Note:
            This statistical tensor (32-bin normalized intensity histogram, channel means,
            standard deviation, and Laplacian texture variance) serves as the baseline
            visual representation for consensus memory evidence fusion, designed to be
            later augmented with high-dimensional foundation model embeddings.

        Args:
            image: OpenCV BGR/RGB image array of the registered architectural region.

        Returns:
            Dict[str, Any]: Standardized JSON-safe dictionary containing histogram and stats.
        """
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            # Safe statistical fallback representation
            return {
                "histogram": [round(1.0 / 32, 5)] * 32,
                "mean_intensity": 128.0,
                "std_intensity": 40.0,
                "laplacian_variance": 100.0,
                "channels_mean": [128.0, 128.0, 128.0],
            }

        try:
            # Grayscale intensity histogram (32 bins)
            gray = (
                cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                if len(image.shape) == 3
                else image
            )
            hist = cv2.calcHist([gray], [0], None, [32], [0, 256]).flatten()
            total_pixels = float(np.sum(hist))
            if total_pixels > 0:
                hist = hist / total_pixels
            else:
                hist = np.ones(32, dtype=np.float32) / 32.0

            hist_list = [round(float(v), 5) for v in hist]

            # Texture & intensity statistics
            mean_intensity = float(np.mean(gray))
            std_intensity = float(np.std(gray))
            lap_var = compute_laplacian_variance(image)

            # 3-channel BGR means
            if len(image.shape) == 3 and image.shape[2] >= 3:
                ch_means = [round(float(np.mean(image[:, :, i])), 3) for i in range(3)]
            else:
                ch_means = [round(mean_intensity, 3)] * 3

            return {
                "histogram": hist_list,
                "mean_intensity": round(mean_intensity, 3),
                "std_intensity": round(std_intensity, 3),
                "laplacian_variance": round(float(lap_var), 3),
                "channels_mean": ch_means,
            }
        except Exception as err:
            logger.warning(f"Error computing feature representation: {err}")
            return {
                "histogram": [round(1.0 / 32, 5)] * 32,
                "mean_intensity": 128.0,
                "std_intensity": 40.0,
                "laplacian_variance": 100.0,
                "channels_mean": [128.0, 128.0, 128.0],
            }

    def _extract_image_features(
        self, observation: Observation, image: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Extract feature representation from image array or disk file."""
        if image is not None and isinstance(image, np.ndarray) and image.size > 0:
            return self._compute_feature_representation(image)

        image_url = getattr(observation, "image_url", None)
        if image_url:
            path = Path(image_url)
            if path.exists():
                try:
                    loaded_img = load_image_cv2(str(path))
                    return self._compute_feature_representation(loaded_img)
                except Exception:
                    pass

        # Fallback from observation triage scores if image is unavailable on disk
        sharpness = getattr(observation, "sharpness_score", 0.5) or 0.5
        exposure = getattr(observation, "exposure_score", 0.5) or 0.5
        quality = getattr(observation, "overall_quality_score", 0.5) or 0.5

        return {
            "histogram": [round(1.0 / 32, 5)] * 32,
            "mean_intensity": round(float(exposure) * 255.0, 3),
            "std_intensity": 40.0,
            "laplacian_variance": round(float(sharpness) * 120.0, 3),
            "channels_mean": [round(float(quality) * 200.0, 3)] * 3,
        }

    # -------------------------------------------------------------------------
    # 3. Initialize Consensus State (Cold Start)
    # -------------------------------------------------------------------------
    def initialize_consensus_state(
        self,
        region_id: Union[uuid.UUID, str],
        observation: Observation,
        db: Session,
        image: Optional[np.ndarray] = None,
    ) -> ConsensusState:
        """Initialize version 1 ConsensusState for a region's first-ever observation.

        Args:
            region_id: Region UUID or identifier.
            observation: First observation record.
            db: SQLAlchemy database session.
            image: Optional image array.

        Returns:
            ConsensusState: Newly initialized ConsensusState record.
        """
        region_uuid = self._resolve_uuid(region_id)
        reliability = float(getattr(observation, "reliability_score", 0.5) or 0.5)
        feature_tensor = self._extract_image_features(observation, image=image)

        new_state = ConsensusState(
            region_id=region_uuid,
            version=1,
            cumulative_reliability=round(reliability, 4),
            observation_count=1,
            structural_health_index=1.0,  # Assume pristine/healthy until defect proven
            consensus_tensor=feature_tensor,
            last_updated_by_observation_id=getattr(observation, "id", None),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(new_state)
        db.commit()
        db.refresh(new_state)
        logger.info(
            f"Initialized version 1 ConsensusState for Region ID {region_uuid} "
            f"with initial reliability {reliability:.4f}"
        )
        return new_state

    # -------------------------------------------------------------------------
    # 4. Bayesian Reliability-Weighted Running Update
    # -------------------------------------------------------------------------
    def update_consensus_state(
        self,
        region_id: Union[uuid.UUID, str],
        observation: Observation,
        db: Session,
        image: Optional[np.ndarray] = None,
    ) -> ConsensusState:
        """Perform reliability-weighted running Bayesian update on active ConsensusState.

        Formula:
            new_tensor = (old_tensor * W_old + new_obs_tensor * w_new) / (W_old + w_new)
            W_old += w_new
            observation_count += 1

        Args:
            region_id: Region UUID or identifier.
            observation: New observation record.
            db: SQLAlchemy database session.
            image: Optional image array.

        Returns:
            ConsensusState: Updated active ConsensusState record.
        """
        region_uuid = self._resolve_uuid(region_id)
        active_state = self.get_active_consensus_state(region_uuid, db)

        if active_state is None:
            return self.initialize_consensus_state(region_uuid, observation, db, image=image)

        # Handle post-reset state with empty tensor
        if active_state.consensus_tensor is None:
            feature_tensor = self._extract_image_features(observation, image=image)
            reliability = float(getattr(observation, "reliability_score", 0.5) or 0.5)
            active_state.consensus_tensor = feature_tensor
            active_state.cumulative_reliability = round(reliability, 4)
            active_state.observation_count = 1
            active_state.last_updated_by_observation_id = getattr(observation, "id", None)
            active_state.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(active_state)
            return active_state

        old_tensor = active_state.consensus_tensor or {}
        new_obs_tensor = self._extract_image_features(observation, image=image)

        w_old = float(active_state.cumulative_reliability or 0.0)
        w_new = float(getattr(observation, "reliability_score", 0.5) or 0.5)
        w_total = w_old + w_new
        if w_total <= 0.0:
            w_total = 1.0

        # Reliability-adaptive blending of histogram bins
        old_hist = np.array(
            old_tensor.get("histogram", [1.0 / 32] * 32), dtype=np.float32
        )
        new_hist = np.array(
            new_obs_tensor.get("histogram", [1.0 / 32] * 32), dtype=np.float32
        )
        blended_hist = (old_hist * w_old + new_hist * w_new) / w_total
        blended_hist_list = [round(float(v), 5) for v in blended_hist]

        # Reliability-adaptive blending of scalar and vector metrics
        def blend_metric(key: str, default: Any) -> Any:
            v_old = old_tensor.get(key, default)
            v_new = new_obs_tensor.get(key, default)
            if isinstance(v_old, list) and isinstance(v_new, list):
                arr_old = np.array(v_old, dtype=np.float32)
                arr_new = np.array(v_new, dtype=np.float32)
                return [
                    round(float(x), 3)
                    for x in (arr_old * w_old + arr_new * w_new) / w_total
                ]
            try:
                val = (float(v_old) * w_old + float(v_new) * w_new) / w_total
                return round(float(val), 3)
            except (ValueError, TypeError):
                return v_new

        blended_tensor = {
            "histogram": blended_hist_list,
            "mean_intensity": blend_metric("mean_intensity", 128.0),
            "std_intensity": blend_metric("std_intensity", 40.0),
            "laplacian_variance": blend_metric("laplacian_variance", 100.0),
            "channels_mean": blend_metric("channels_mean", [128.0, 128.0, 128.0]),
        }

        # Update the active ConsensusState row (preserve version, do not touch structural_health_index)
        active_state.consensus_tensor = blended_tensor
        active_state.cumulative_reliability = round(w_total, 4)
        active_state.observation_count = int(active_state.observation_count or 0) + 1
        active_state.last_updated_by_observation_id = getattr(observation, "id", None)
        active_state.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(active_state)
        logger.debug(
            f"Updated ConsensusState v{active_state.version} for Region ID {region_uuid} "
            f"(count={active_state.observation_count}, cum_rel={active_state.cumulative_reliability:.3f})"
        )
        return active_state

    # -------------------------------------------------------------------------
    # 5. Create New Consensus Version (Explicit Major Recalibration / Reset)
    # -------------------------------------------------------------------------
    def create_new_consensus_version(
        self,
        region_id: Union[uuid.UUID, str],
        reason: Optional[str],
        db: Session,
    ) -> ConsensusState:
        """Create a new incremented ConsensusState version for major repairs or resets.

        Preserves existing versions in historical records while starting a fresh baseline.

        Args:
            region_id: Region UUID or identifier.
            reason: Justification note for version reset (e.g., 'Restoration work completed').
            db: SQLAlchemy database session.

        Returns:
            ConsensusState: Newly created incremented version ConsensusState.
        """
        region_uuid = self._resolve_uuid(region_id)
        latest_state = self.get_active_consensus_state(region_uuid, db)
        next_version = (latest_state.version + 1) if latest_state else 1

        new_version_state = ConsensusState(
            region_id=region_uuid,
            version=next_version,
            cumulative_reliability=0.0,
            observation_count=0,
            structural_health_index=1.0,
            consensus_tensor=None,  # Initialized fresh by next incoming observation
            reset_reason=reason,
            last_updated_by_observation_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(new_version_state)
        db.commit()
        db.refresh(new_version_state)
        logger.info(
            f"Created new ConsensusState version {next_version} for Region ID {region_uuid} "
            f"(reason='{reason}')"
        )
        return new_version_state

    # -------------------------------------------------------------------------
    # 6. Unified Processing Pipeline Entry Point
    # -------------------------------------------------------------------------
    def process_observation(
        self,
        observation: Observation,
        db: Session,
        image: Optional[np.ndarray] = None,
    ) -> Optional[ConsensusState]:
        """Unified entry point to incorporate an observation into regional consensus memory.

        Args:
            observation: Observation record to process.
            db: SQLAlchemy database session.
            image: Optional image array.

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
                image=image,
            )

        return self.update_consensus_state(
            region_id=observation.region_id,
            observation=observation,
            db=db,
            image=image,
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
