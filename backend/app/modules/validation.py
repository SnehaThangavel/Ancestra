"""Module 4: SSIM Structural Anomaly Detection & Defect Validation.

SESCI Architecture - Module 4 (Validation):
Performs full-reference Structural Similarity Index (SSIM) comparison between a new
observation and the region's active baseline observation (established in Module 3).
Isolates defect bounding boxes via differential error map thresholding and morphology,
computes severity scores, and updates regional structural health indicators without
requiring multi-observer crowdsourced corroboration.
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List, Union
import numpy as np
import cv2
from skimage.metrics import structural_similarity as ssim
from sqlalchemy.orm import Session

from app.config import settings
from app.models.observation import Observation
from app.models.consensus_state import ConsensusState
from app.models.validation import AnomalyValidation
from app.schemas.validation import AnomalyValidationResponse
from app.utils.image_utils import load_image_cv2
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ValidationModule:
    """Module 4 implementation: Full-reference SSIM anomaly detection and defect validation."""

    def __init__(self, default_ssim_threshold: float = 0.85) -> None:
        """Initialize validation module parameters.

        Args:
            default_ssim_threshold: Minimum SSIM score below which structural differences are flagged as anomalies.
        """
        self.default_ssim_threshold = default_ssim_threshold

    # -------------------------------------------------------------------------
    # 1. Image Loading Utility
    # -------------------------------------------------------------------------
    def _load_observation_cv2(self, obs: Observation) -> np.ndarray:
        """Load OpenCV image array from observation record."""
        if obs is None or not obs.image_url:
            raise ValueError(f"Observation {getattr(obs, 'id', 'unknown')} has no associated image_url.")

        # Check candidate file paths
        candidate_paths = [
            obs.image_url,
            os.path.join(getattr(settings, "UPLOAD_DIR", "./uploads"), os.path.basename(obs.image_url)),
            os.path.join("./uploads", os.path.basename(obs.image_url)),
            os.path.join(".", obs.image_url),
        ]
        for path_str in candidate_paths:
            if os.path.exists(path_str):
                try:
                    img = load_image_cv2(path_str)
                    if img is not None and img.size > 0:
                        return img
                except Exception:
                    pass

        # Also search in uploads directory for matching observation ID or monument/region prefix
        upload_dir = getattr(settings, "UPLOAD_DIR", "./uploads")
        if os.path.exists(upload_dir):
            obs_id_str = str(obs.id)[:8]
            reg_id_str = str(obs.region_id)[:8] if obs.region_id else ""
            for fname in os.listdir(upload_dir):
                if (obs_id_str in fname) or (reg_id_str and reg_id_str in fname):
                    candidate_file = os.path.join(upload_dir, fname)
                    try:
                        img = load_image_cv2(candidate_file)
                        if img is not None and img.size > 0:
                            return img
                    except Exception:
                        pass

        raise FileNotFoundError(
            f"Image file for observation {obs.id} ('{obs.image_url}') was not found on disk."
        )

    # -------------------------------------------------------------------------
    # 2. Core SSIM & Defect Bounding Box Computation
    # -------------------------------------------------------------------------
    def compute_ssim_comparison(
        self,
        query_image: np.ndarray,
        baseline_image: np.ndarray,
        ssim_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Compute SSIM delta and extract defect bounding boxes from the differential error map.

        Args:
            query_image: Query observation image array.
            baseline_image: Registered baseline observation image array.
            ssim_threshold: Threshold below which anomalies are flagged (default: 0.85).

        Returns:
            Dict[str, Any]: Comprehensive comparison dictionary including ssim_score,
                ssim_delta, severity_score, anomaly_detected, anomaly_type, and defect_bounding_boxes.
        """
        threshold = ssim_threshold if ssim_threshold is not None else self.default_ssim_threshold

        if query_image is None or baseline_image is None or query_image.size == 0 or baseline_image.size == 0:
            return {
                "anomaly_detected": False,
                "anomaly_type": None,
                "ssim_score": 1.0,
                "ssim_delta": 0.0,
                "severity_score": 0.0,
                "defect_bounding_boxes": [],
            }

        # Convert to Grayscale
        gray_query = cv2.cvtColor(query_image, cv2.COLOR_BGR2GRAY) if len(query_image.shape) == 3 else query_image
        gray_base = cv2.cvtColor(baseline_image, cv2.COLOR_BGR2GRAY) if len(baseline_image.shape) == 3 else baseline_image

        # Resize query image to match baseline if dimensions mismatch
        if gray_query.shape != gray_base.shape:
            gray_query = cv2.resize(gray_query, (gray_base.shape[1], gray_base.shape[0]), interpolation=cv2.INTER_AREA)

        # Compute full-reference structural similarity
        score, diff = ssim(gray_base, gray_query, full=True)
        ssim_score = max(0.0, min(1.0, float(score)))
        ssim_delta = max(0.0, round(1.0 - ssim_score, 4))

        # Difference map: values near 0 mean identical, values near 255 mean maximum difference
        diff_map = np.clip((1.0 - diff) * 255.0, 0, 255).astype(np.uint8)

        # Isolate defect regions via Otsu thresholding + morphological cleanup
        _, thresh = cv2.threshold(diff_map, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)

        # Find defect contours
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        defect_bounding_boxes: List[List[int]] = []
        total_defect_area = 0.0
        img_area = float(gray_base.shape[0] * gray_base.shape[1])
        max_aspect_ratio = 1.0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= 35:  # Filter out minor sensor/lighting noise
                x, y, w, h = cv2.boundingRect(cnt)
                defect_bounding_boxes.append([int(x), int(y), int(w), int(h)])
                total_defect_area += area
                aspect_ratio = max(float(w) / max(1.0, float(h)), float(h) / max(1.0, float(w)))
                if aspect_ratio > max_aspect_ratio:
                    max_aspect_ratio = aspect_ratio

        defect_area_ratio = min(1.0, total_defect_area / max(1.0, img_area))

        # Severity is a weighted composite of structural difference magnitude and surface defect fraction
        severity_score = min(1.0, max(0.0, round(0.50 * ssim_delta + 0.50 * min(1.0, defect_area_ratio * 8.0), 4)))
        anomaly_detected = (len(defect_bounding_boxes) > 0) or (ssim_score < threshold) or (severity_score >= 0.05)

        # Defect categorization
        anomaly_type: Optional[str] = None
        if anomaly_detected:
            if max_aspect_ratio >= 2.5:
                anomaly_type = "crack"
            elif defect_area_ratio >= 0.05:
                anomaly_type = "spalling"
            elif ssim_delta >= 0.15:
                anomaly_type = "surface_deterioration"
            else:
                anomaly_type = "discoloration"

        return {
            "anomaly_detected": anomaly_detected,
            "anomaly_type": anomaly_type,
            "ssim_score": round(ssim_score, 4),
            "ssim_delta": ssim_delta,
            "severity_score": severity_score,
            "defect_bounding_boxes": defect_bounding_boxes,
        }

    # -------------------------------------------------------------------------
    # 3. Main Verification Pipeline
    # -------------------------------------------------------------------------
    def validate_observation(
        self,
        observation_id: Union[uuid.UUID, str],
        db: Session,
        region_id: Optional[Union[uuid.UUID, str]] = None,
        ssim_threshold: Optional[float] = None,
    ) -> AnomalyValidationResponse:
        """Run SSIM anomaly comparison for an observation against the regional baseline.

        Args:
            observation_id: Target observation UUID or string identifier.
            db: SQLAlchemy database session.
            region_id: Optional region UUID override.
            ssim_threshold: Optional SSIM detection threshold.

        Returns:
            AnomalyValidationResponse: Detailed validation response.
        """
        obs_uuid = self._resolve_uuid(observation_id)
        obs_record = db.query(Observation).filter(Observation.id == obs_uuid).first()
        if not obs_record:
            raise ValueError(f"Observation with ID '{observation_id}' not found.")

        # Determine target region
        effective_region_id = self._resolve_uuid(region_id) if region_id is not None else obs_record.region_id
        if effective_region_id is None:
            raise ValueError("Observation does not have an associated region_id.")

        # Fetch active ConsensusState for this region to find the baseline pointer
        active_state = (
            db.query(ConsensusState)
            .filter(ConsensusState.region_id == effective_region_id)
            .order_by(ConsensusState.version.desc())
            .first()
        )

        # Edge Case: Cold-start or Observation IS the baseline itself
        if active_state is None or active_state.baseline_observation_id is None or active_state.baseline_observation_id == obs_record.id:
            logger.info(
                f"Observation {obs_uuid} is the baseline photo for region {effective_region_id}; no comparison available."
            )
            return AnomalyValidationResponse(
                region_id=effective_region_id,
                observation_id=obs_uuid,
                baseline_observation_id=obs_uuid,
                anomaly_detected=False,
                anomaly_type=None,
                ssim_score=1.0,
                ssim_delta=0.0,
                severity_score=0.0,
                defect_bounding_boxes=[],
                corroboration_count=1,
                is_confirmed=True,
                is_baseline=True,
                message="Observation is the baseline photo; no comparison available yet.",
                created_at=datetime.now(timezone.utc),
            )

        # Fetch baseline observation
        baseline_obs = db.query(Observation).filter(Observation.id == active_state.baseline_observation_id).first()
        if not baseline_obs:
            logger.warning(
                f"Baseline observation {active_state.baseline_observation_id} not found in DB."
            )
            return AnomalyValidationResponse(
                region_id=effective_region_id,
                observation_id=obs_uuid,
                baseline_observation_id=active_state.baseline_observation_id,
                anomaly_detected=False,
                anomaly_type=None,
                ssim_score=1.0,
                ssim_delta=0.0,
                severity_score=0.0,
                defect_bounding_boxes=[],
                corroboration_count=1,
                is_confirmed=True,
                is_baseline=False,
                message="Baseline observation record unavailable for comparison.",
                created_at=datetime.now(timezone.utc),
            )

        # Load images
        query_cv2 = self._load_observation_cv2(obs_record)
        baseline_cv2 = self._load_observation_cv2(baseline_obs)

        # Perform SSIM defect detection
        comparison = self.compute_ssim_comparison(
            query_image=query_cv2,
            baseline_image=baseline_cv2,
            ssim_threshold=ssim_threshold,
        )

        # Persist AnomalyValidation record in PostgreSQL
        validation_record = AnomalyValidation(
            region_id=effective_region_id,
            anomaly_type=comparison["anomaly_type"] or "structural_condition",
            ssim_delta=comparison["ssim_delta"],
            severity_score=comparison["severity_score"],
            corroboration_count=1,
            corroborating_observation_ids=[obs_uuid],
            is_confirmed=True,
            defect_polygon={
                "bounding_boxes": comparison["defect_bounding_boxes"],
                "ssim_score": comparison["ssim_score"],
                "baseline_observation_id": str(active_state.baseline_observation_id),
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(validation_record)

        # Update region's active ConsensusState structural_health_index
        new_health = max(0.0, min(1.0, round(1.0 - comparison["severity_score"], 4)))
        active_state.structural_health_index = new_health
        active_state.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(validation_record)
        db.refresh(active_state)

        logger.info(
            f"Validated observation {obs_uuid} against baseline {active_state.baseline_observation_id} "
            f"(SSIM={comparison['ssim_score']}, anomaly={comparison['anomaly_detected']}, health={new_health})"
        )

        return AnomalyValidationResponse(
            validation_id=validation_record.id,
            observation_id=obs_uuid,
            baseline_observation_id=active_state.baseline_observation_id,
            region_id=effective_region_id,
            anomaly_detected=comparison["anomaly_detected"],
            anomaly_type=comparison["anomaly_type"],
            ssim_score=comparison["ssim_score"],
            ssim_delta=comparison["ssim_delta"],
            severity_score=comparison["severity_score"],
            defect_bounding_boxes=comparison["defect_bounding_boxes"],
            corroboration_count=1,
            is_confirmed=True,
            is_baseline=False,
            message="Anomaly detected" if comparison["anomaly_detected"] else "Structural condition verified healthy",
            created_at=validation_record.created_at,
        )

    # -------------------------------------------------------------------------
    # 4. Query Validation History
    # -------------------------------------------------------------------------
    def get_region_validations(
        self, region_id: Union[uuid.UUID, str], db: Session
    ) -> List[AnomalyValidation]:
        """Fetch all validation findings for an architectural region.

        Args:
            region_id: Region UUID or string identifier.
            db: SQLAlchemy database session.

        Returns:
            List[AnomalyValidation]: Chronological list of validation records.
        """
        reg_uuid = self._resolve_uuid(region_id)
        return (
            db.query(AnomalyValidation)
            .filter(AnomalyValidation.region_id == reg_uuid)
            .order_by(AnomalyValidation.created_at.desc())
            .all()
        )

    def get_observation_validation(
        self, observation_id: Union[uuid.UUID, str], db: Session
    ) -> Optional[AnomalyValidation]:
        """Fetch the validation record associated with a specific observation.

        Args:
            observation_id: Observation UUID or string identifier.
            db: SQLAlchemy database session.

        Returns:
            Optional[AnomalyValidation]: AnomalyValidation record or None.
        """
        obs_uuid = self._resolve_uuid(observation_id)
        obs_str = str(obs_uuid)
        validations = db.query(AnomalyValidation).order_by(AnomalyValidation.created_at.desc()).all()
        for v in validations:
            c_ids = v.corroborating_observation_ids
            if c_ids and isinstance(c_ids, (list, tuple)):
                if any(str(item) == obs_str for item in c_ids):
                    return v
            elif c_ids and str(c_ids) == obs_str:
                return v
        return None

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


def get_validation_module() -> ValidationModule:
    """Factory function providing a configured ValidationModule instance."""
    return ValidationModule()
