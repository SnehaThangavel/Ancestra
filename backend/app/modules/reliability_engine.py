"""Module 2: Six-Factor Dynamic Reliability Coefficient Engine.

SESCI Architecture - Patent Claim Scope:
Computes a composite reliability coefficient R_i in [0, 1] for every photo observation,
which downstream modules (consensus_memory.py, validation.py) use to weight how much
each photograph influences the system's understanding of an architectural region's condition.

The six weighted factors:
1. Image Quality Factor (f_quality): Derived from overall_quality_score with non-linear penalty curve.
2. Geometric Consistency Factor (f_geom): Derived from ORB/RANSAC registration_confidence with failure floor.
3. Viewpoint Diversity Factor (f_view): Rewards distinct vantage perspectives relative to 90-day regional history.
4. Temporal Relevance Factor (f_temp): Exponential time-decay based on observation age and half-life.
5. Environmental Similarity Factor (f_env): Lighting/exposure deviation from historical regional mean.
6. Consensus Agreement Factor (f_agree): Structural/feature similarity against existing consensus memory state.
"""

from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timezone, timedelta
from pathlib import Path
import numpy as np
import cv2
from sqlalchemy.orm import Session

from app.config import settings
from app.models.observation import Observation
from app.models.consensus_state import ConsensusState
from app.schemas.reliability import ReliabilityFactors
from app.utils.image_utils import load_image_cv2
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ReliabilityEngineModule:
    """Production-grade implementation of Module 2: Dynamic Reliability Coefficient Engine."""

    def __init__(
        self,
        default_weights: Optional[Dict[str, float]] = None,
        half_life_days: Optional[float] = None,
    ) -> None:
        """Initialize reliability weight parameters and temporal decay settings.

        Args:
            default_weights: Optional dictionary of factor weights summing to 1.0.
            half_life_days: Half-life in days for exponential temporal relevance decay.
        """
        self.weights = default_weights or getattr(
            settings,
            "RELIABILITY_WEIGHTS",
            {
                "image_quality": 0.25,
                "geometric_consistency": 0.20,
                "viewpoint_diversity": 0.10,
                "temporal_relevance": 0.15,
                "environmental_similarity": 0.10,
                "agreement": 0.20,
            },
        )
        self.half_life_days = half_life_days or getattr(
            settings, "RELIABILITY_TEMPORAL_HALF_LIFE_DAYS", 180.0
        )

    # -------------------------------------------------------------------------
    # 1. Image Quality Factor
    # -------------------------------------------------------------------------
    def compute_image_quality_factor(
        self, observation: Union[Observation, Dict[str, Any]]
    ) -> float:
        """Compute the Image Quality Factor (f_quality) in [0.0, 1.0].

        Directly derived from Module 1's overall_quality_score, applying a mild
        non-linear power curve (score ** 1.5) so borderline-quality photos get
        disproportionately downweighted relative to clearly high-quality photos.

        Args:
            observation: Observation ORM instance or dictionary with quality metrics.

        Returns:
            float: Quality factor in [0.0, 1.0].
        """
        if observation is None:
            return 0.0

        score = (
            getattr(observation, "overall_quality_score", None)
            if not isinstance(observation, dict)
            else observation.get("overall_quality_score")
        )

        if score is None:
            sharpness = (
                getattr(observation, "sharpness_score", 0.0)
                if not isinstance(observation, dict)
                else observation.get("sharpness_score", 0.0)
            )
            score = sharpness or 0.0

        try:
            score_val = float(score)
        except (ValueError, TypeError):
            score_val = 0.0

        # Apply mild non-linear penalty curve
        clamped_score = float(np.clip(score_val, 0.0, 1.0))
        curved_score = float(np.clip(clamped_score**1.5, 0.0, 1.0))
        return round(curved_score, 4)

    # -------------------------------------------------------------------------
    # 2. Geometric Consistency Factor
    # -------------------------------------------------------------------------
    def compute_geometric_consistency_factor(
        self, observation: Union[Observation, Dict[str, Any]]
    ) -> float:
        """Compute the Geometric Consistency Factor (f_geom) in [0.0, 1.0].

        Derived from Module 1's registration_confidence (ORB/RANSAC inlier ratio).
        If registration_success is False, returns a low fixed floor value (0.1)
        rather than 0.0, preserving low-weight signal for unaligned photos.

        Args:
            observation: Observation ORM instance or dictionary with registration metrics.

        Returns:
            float: Geometric consistency factor in [0.0, 1.0].
        """
        if observation is None:
            return 0.1

        reg_success = (
            getattr(observation, "registration_success", False)
            if not isinstance(observation, dict)
            else observation.get("registration_success", False)
        )
        reg_conf = (
            getattr(observation, "registration_confidence", None)
            if not isinstance(observation, dict)
            else observation.get("registration_confidence")
        )

        if not reg_success or reg_conf is None:
            return 0.1

        try:
            conf_val = float(reg_conf)
        except (ValueError, TypeError):
            conf_val = 0.1

        return round(float(np.clip(max(0.1, conf_val), 0.0, 1.0)), 4)

    # -------------------------------------------------------------------------
    # 3. Viewpoint Diversity Factor
    # -------------------------------------------------------------------------
    def compute_viewpoint_diversity_factor(
        self,
        observation: Union[Observation, Dict[str, Any]],
        db: Optional[Session] = None,
    ) -> float:
        """Compute the Viewpoint Diversity Factor (f_view) in [0.0, 1.0].

        Queries prior observations for the same region_id within a 90-day window.
        Rewards observations that add distinct vantage perspectives or camera sources
        over near-duplicate viewing angles. Defaults to neutral 0.5 when no prior
        regional history exists.

        Args:
            observation: Observation ORM instance or dictionary.
            db: Optional SQLAlchemy database session.

        Returns:
            float: Viewpoint diversity factor in [0.0, 1.0].
        """
        if observation is None or db is None:
            return 0.5

        region_id = (
            getattr(observation, "region_id", None)
            if not isinstance(observation, dict)
            else observation.get("region_id")
        )
        if not region_id:
            return 0.5

        obs_id = (
            getattr(observation, "id", None)
            if not isinstance(observation, dict)
            else observation.get("id")
        )

        obs_dt = self._extract_datetime(observation)
        window_start = obs_dt - timedelta(days=90)

        try:
            query = db.query(Observation).filter(
                Observation.region_id == region_id,
                Observation.created_at >= window_start,
            )
            if obs_id:
                query = query.filter(Observation.id != obs_id)
            prior_obs = query.all()
        except Exception as err:
            logger.warning(f"Error querying prior observations for viewpoint diversity: {err}")
            return 0.5

        if not prior_obs:
            return 0.5

        # Compare vantage parameters: EXIF orientation, user_id, camera model, resolution
        current_exif = (
            getattr(observation, "exif_data", None)
            if not isinstance(observation, dict)
            else observation.get("exif_data")
        ) or {}
        current_orient = current_exif.get("orientation") if isinstance(current_exif, dict) else None
        current_make = current_exif.get("camera_make") if isinstance(current_exif, dict) else None
        current_user = (
            getattr(observation, "user_id", None)
            if not isinstance(observation, dict)
            else observation.get("user_id")
        )

        duplicate_count = 0
        for prior in prior_obs:
            p_exif = prior.exif_data or {}
            p_orient = p_exif.get("orientation") if isinstance(p_exif, dict) else None
            p_make = p_exif.get("camera_make") if isinstance(p_exif, dict) else None
            p_user = prior.user_id

            # Check if this prior observation is a near-duplicate vantage
            same_user = bool(current_user and p_user and current_user == p_user)
            same_orient = bool(current_orient is not None and p_orient is not None and current_orient == p_orient)
            same_camera = bool(current_make and p_make and current_make == p_make)

            if same_user and same_orient and same_camera:
                duplicate_count += 1

        total_prior = len(prior_obs)
        duplicate_ratio = duplicate_count / float(total_prior)

        # High duplicate ratio -> lower diversity reward; diverse sources -> higher reward
        diversity_score = 0.5 + 0.4 * (1.0 - duplicate_ratio) - 0.2 * min(1.0, duplicate_count / 5.0)
        return round(float(np.clip(diversity_score, 0.1, 1.0)), 4)

    # -------------------------------------------------------------------------
    # 4. Temporal Relevance Factor
    # -------------------------------------------------------------------------
    def compute_temporal_relevance_factor(
        self, observation: Union[Observation, Dict[str, Any]]
    ) -> float:
        """Compute the Temporal Relevance Factor (f_temp) in [0.0, 1.0].

        Applies an exponential decay curve relative to the current time, parameterized
        by the configurable half-life (RELIABILITY_TEMPORAL_HALF_LIFE_DAYS). Old photos
        retain a non-zero baseline weight (floor 0.15).

        Args:
            observation: Observation ORM instance or dictionary with timestamps.

        Returns:
            float: Temporal relevance factor in [0.0, 1.0].
        """
        if observation is None:
            return 0.5

        obs_dt = self._extract_datetime(observation)
        now = datetime.now(timezone.utc)

        age_seconds = max(0.0, (now - obs_dt).total_seconds())
        age_days = age_seconds / 86400.0

        # Half-life exponential decay: decay = exp(-ln(2) * (t / half_life))
        half_life = max(1.0, float(self.half_life_days))
        decay = float(np.exp(-np.log(2.0) * (age_days / half_life)))

        # Preserve a non-zero floor for historical baseline photographs
        score = 0.15 + 0.85 * decay
        return round(float(np.clip(score, 0.0, 1.0)), 4)

    # -------------------------------------------------------------------------
    # 5. Environmental Similarity Factor
    # -------------------------------------------------------------------------
    def compute_environmental_similarity_factor(
        self,
        observation: Union[Observation, Dict[str, Any]],
        db: Optional[Session] = None,
    ) -> float:
        """Compute the Environmental Similarity Factor (f_env) in [0.0, 1.0].

        Compares this observation's exposure and lighting characteristics against
        the historical average for this region's prior observations. Wild deviations
        score lower due to inconsistent lighting reducing visual comparison reliability.
        Defaults to neutral 0.5 if fewer than 3 prior observations exist.

        Args:
            observation: Observation ORM instance or dictionary.
            db: Optional SQLAlchemy database session.

        Returns:
            float: Environmental similarity factor in [0.0, 1.0].
        """
        if observation is None or db is None:
            return 0.5

        region_id = (
            getattr(observation, "region_id", None)
            if not isinstance(observation, dict)
            else observation.get("region_id")
        )
        if not region_id:
            return 0.5

        obs_id = (
            getattr(observation, "id", None)
            if not isinstance(observation, dict)
            else observation.get("id")
        )

        try:
            query = db.query(Observation).filter(
                Observation.region_id == region_id,
                Observation.exposure_score.isnot(None),
            )
            if obs_id:
                query = query.filter(Observation.id != obs_id)
            prior_obs = query.all()
        except Exception as err:
            logger.warning(f"Error querying historical exposure for environmental factor: {err}")
            return 0.5

        valid_exposures = [
            float(p.exposure_score)
            for p in prior_obs
            if p.exposure_score is not None
        ]

        # Not enough history to establish an environmental baseline
        if len(valid_exposures) < 3:
            return 0.5

        mean_exposure = sum(valid_exposures) / float(len(valid_exposures))

        current_exposure = (
            getattr(observation, "exposure_score", None)
            if not isinstance(observation, dict)
            else observation.get("exposure_score")
        )
        if current_exposure is None:
            return 0.5

        try:
            curr_exp_val = float(current_exposure)
        except (ValueError, TypeError):
            return 0.5

        # Measure deviation from regional historical exposure mean
        exposure_deviation = abs(curr_exp_val - mean_exposure)
        score = max(0.0, 1.0 - 2.0 * exposure_deviation)
        return round(float(np.clip(score, 0.0, 1.0)), 4)

    # -------------------------------------------------------------------------
    # 6. Consensus Agreement Factor
    # -------------------------------------------------------------------------
    def compute_agreement_factor(
        self,
        observation: Union[Observation, Dict[str, Any]],
        db: Optional[Session] = None,
    ) -> float:
        """Compute the Consensus Agreement Factor (f_agree) in [0.0, 1.0].

        Measures visual/feature structural similarity between this observation
        and the region's current ConsensusState tensor. Defaults to 1.0 if no
        prior consensus state exists (initial baseline observation).

        Args:
            observation: Observation ORM instance or dictionary.
            db: Optional SQLAlchemy database session.

        Returns:
            float: Agreement factor in [0.0, 1.0].
        """
        if observation is None:
            return 1.0

        region_id = (
            getattr(observation, "region_id", None)
            if not isinstance(observation, dict)
            else observation.get("region_id")
        )
        if not region_id or db is None:
            return 1.0

        try:
            consensus = (
                db.query(ConsensusState)
                .filter(ConsensusState.region_id == region_id)
                .order_by(ConsensusState.version.desc())
                .first()
            )
        except Exception as err:
            logger.warning(f"Error querying consensus state for agreement factor: {err}")
            return 1.0

        # Initial observation for region -> perfect agreement by definition
        if consensus is None or consensus.consensus_tensor is None:
            return 1.0

        # Compute structural / histogram similarity if image is available on disk
        image_url = (
            getattr(observation, "image_url", None)
            if not isinstance(observation, dict)
            else observation.get("image_url")
        )

        tensor_data = consensus.consensus_tensor
        if isinstance(tensor_data, dict) and "histogram" in tensor_data and image_url:
            img_path = Path(image_url)
            if img_path.exists():
                try:
                    cv_img = load_image_cv2(str(img_path))
                    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                    hist = cv2.calcHist([gray], [0], None, [32], [0, 256])
                    cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

                    ref_hist = np.array(tensor_data["histogram"], dtype=np.float32)
                    sim = cv2.compareHist(hist, ref_hist, cv2.HISTCMP_CORREL)
                    # Convert correlation [-1, 1] to [0, 1]
                    normalized_sim = float(np.clip((sim + 1.0) / 2.0, 0.0, 1.0))
                    return round(normalized_sim, 4)
                except Exception as hist_err:
                    logger.warning(f"Histogram comparison error: {hist_err}")

        # Feature / structural health alignment fallback
        health_index = getattr(consensus, "structural_health_index", 1.0) or 1.0
        quality_score = (
            getattr(observation, "overall_quality_score", 1.0)
            if not isinstance(observation, dict)
            else observation.get("overall_quality_score", 1.0)
        ) or 1.0

        # Health & quality consistency metric
        agreement_score = 1.0 - 0.4 * abs(float(health_index) - float(quality_score))
        return round(float(np.clip(agreement_score, 0.0, 1.0)), 4)

    # -------------------------------------------------------------------------
    # 7. Composite Reliability Computation & Persistence
    # -------------------------------------------------------------------------
    def compute_factors(
        self,
        observation: Union[Observation, Dict[str, Any]],
        db: Optional[Session] = None,
    ) -> ReliabilityFactors:
        """Compute all six individual reliability factors for an observation.

        Args:
            observation: Observation ORM instance or dictionary.
            db: Optional database session.

        Returns:
            ReliabilityFactors: Pydantic model with all 6 factor scores.
        """
        f_quality = self.compute_image_quality_factor(observation)
        f_geom = self.compute_geometric_consistency_factor(observation)
        f_view = self.compute_viewpoint_diversity_factor(observation, db=db)
        f_temp = self.compute_temporal_relevance_factor(observation)
        f_env = self.compute_environmental_similarity_factor(observation, db=db)
        f_agree = self.compute_agreement_factor(observation, db=db)

        return ReliabilityFactors(
            image_quality=f_quality,
            geometric_consistency=f_geom,
            viewpoint_diversity=f_view,
            temporal_relevance=f_temp,
            environmental_similarity=f_env,
            agreement=f_agree,
        )

    def compute_reliability(
        self,
        observation: Union[Observation, Dict[str, Any]],
        db: Optional[Session] = None,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Compute weighted composite reliability R_i and persist results to DB.

        Formula:
            R_i = sum(w_k * f_k) for k in factors, clamped to [0.0, 1.0].

        Args:
            observation: Observation record to score.
            db: Optional SQLAlchemy database session for DB queries and persistence.
            custom_weights: Optional override dictionary of factor weights.

        Returns:
            Dict[str, Any]: Dictionary containing 'reliability_score' and 'reliability_factors'.
        """
        factors = self.compute_factors(observation, db=db)
        weights = custom_weights or self.weights

        # Normalize weights to sum to 1.0 if custom weights provided
        total_w = sum(weights.values())
        if total_w <= 0.0:
            total_w = 1.0

        composite_score = sum(
            (weights.get(k, 0.0) / total_w) * getattr(factors, k)
            for k in [
                "image_quality",
                "geometric_consistency",
                "viewpoint_diversity",
                "temporal_relevance",
                "environmental_similarity",
                "agreement",
            ]
        )
        clamped_score = round(float(np.clip(composite_score, 0.0, 1.0)), 4)
        factors_dict = factors.model_dump()

        result = {
            "reliability_score": clamped_score,
            "reliability_factors": factors_dict,
        }

        # Persist score and factors onto Observation ORM row
        if db is not None and isinstance(observation, Observation):
            try:
                observation.reliability_score = clamped_score
                observation.reliability_factors = factors_dict
                db.commit()
                db.refresh(observation)
                logger.debug(
                    f"Updated Observation ID {observation.id} with reliability score {clamped_score:.4f}"
                )
            except Exception as err:
                db.rollback()
                logger.error(f"Failed to persist reliability score to Observation: {err}")
                raise

        return result

    # -------------------------------------------------------------------------
    # Helper Utilities
    # -------------------------------------------------------------------------
    @staticmethod
    def _extract_datetime(observation: Union[Observation, Dict[str, Any]]) -> datetime:
        """Extract offset-aware UTC datetime from observation record."""
        captured = (
            getattr(observation, "captured_at", None)
            if not isinstance(observation, dict)
            else observation.get("captured_at")
        )
        created = (
            getattr(observation, "created_at", None)
            if not isinstance(observation, dict)
            else observation.get("created_at")
        )
        raw_dt = captured or created or datetime.now(timezone.utc)

        if isinstance(raw_dt, str):
            try:
                raw_dt = datetime.fromisoformat(raw_dt)
            except Exception:
                raw_dt = datetime.now(timezone.utc)

        if isinstance(raw_dt, datetime):
            if raw_dt.tzinfo is None:
                return raw_dt.replace(tzinfo=timezone.utc)
            return raw_dt.astimezone(timezone.utc)

        return datetime.now(timezone.utc)


def get_reliability_engine(
    default_weights: Optional[Dict[str, float]] = None,
) -> ReliabilityEngineModule:
    """Factory function providing a configured ReliabilityEngineModule instance."""
    return ReliabilityEngineModule(default_weights=default_weights)
