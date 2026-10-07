"""Module 1: Image Quality Assessment, EXIF Metadata Extraction, AI Region Suggestion, and Alignment.

SESCI Architecture - Module 1 (Ingestion & Registration):
Handles image quality validation (Laplacian variance blur, luminance glare/exposure),
EXIF telemetry parsing (DMS-to-decimal GPS, timestamp, camera make/model),
AI-assisted architectural region suggestion (SAM + OpenCLIP zero-shot classification),
and sequential alignment against the most recent prior observation for the target region.
"""

from typing import Dict, Any, Tuple, Optional, List, Union, BinaryIO
import io
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ExifTags
from sqlalchemy.orm import Session

from app.config import settings
from app.models.observation import Observation
from app.models.region import Region
from app.schemas.ingestion import EXIFMetadata, ImageIngestionResponse, RegionItem, RegionSuggestionResponse
from app.ai import SAMSegmenter, CLIPRegionClassifier, get_sam_segmenter, get_region_classifier
from app.modules.reliability_engine import ReliabilityEngineModule, get_reliability_engine
from app.modules.consensus_memory import ConsensusMemoryModule, get_consensus_memory
from app.utils.image_utils import (
    compute_laplacian_variance,
    detect_glare_ratio,
    load_image_cv2,
    load_image_pil,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ImageIngestionModule:
    """Implementation of Module 1: Image Ingestion, AI Region Suggestion, Quality Assessment & Registration."""

    def __init__(
        self,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        min_blur_var: Optional[float] = None,
        max_glare_ratio: Optional[float] = None,
        min_quality_threshold: Optional[float] = None,
        max_orb_features: Optional[int] = None,
        min_matches: Optional[int] = None,
        ransac_threshold: Optional[float] = None,
        sam_segmenter: Optional[SAMSegmenter] = None,
        region_classifier: Optional[CLIPRegionClassifier] = None,
        use_ai_segmentation: Optional[bool] = None,
        iou_threshold: Optional[float] = None,
        reliability_engine: Optional[ReliabilityEngineModule] = None,
        consensus_memory: Optional[ConsensusMemoryModule] = None,
    ) -> None:
        """Initialize the Image Ingestion module with configurable thresholds and AI models.

        Args:
            min_width: Minimum allowable image width in pixels.
            min_height: Minimum allowable image height in pixels.
            min_blur_var: Minimum Laplacian variance for sharpness acceptable threshold.
            max_glare_ratio: Maximum fraction of glare/saturated pixels before rejection.
            min_quality_threshold: Minimum overall composite quality score [0, 1].
            max_orb_features: Number of ORB features to compute for keypoint matching.
            min_matches: Minimum number of matched keypoints required for homography estimation.
            ransac_threshold: Maximum allowable reprojection error in pixels for RANSAC.
            sam_segmenter: Injected SAMSegmenter instance (created once at app startup).
            region_classifier: Injected CLIPRegionClassifier instance.
            use_ai_segmentation: Flag to toggle AI segmentation vs homography fallback.
            iou_threshold: IoU overlap threshold for matching existing database regions.
            reliability_engine: Optional injected ReliabilityEngineModule.
            consensus_memory: Optional injected ConsensusMemoryModule.
        """
        self.min_width = min_width or getattr(settings, "MIN_IMAGE_WIDTH", 400)
        self.min_height = min_height or getattr(settings, "MIN_IMAGE_HEIGHT", 300)
        self.min_blur_var = min_blur_var or getattr(settings, "BLUR_LAPLACIAN_MIN_VAR", 80.0)
        self.max_glare_ratio = max_glare_ratio or getattr(settings, "GLARE_MAX_RATIO", 0.25)
        self.min_quality_threshold = min_quality_threshold or getattr(
            settings, "MIN_QUALITY_THRESHOLD", 0.35
        )
        self.max_orb_features = max_orb_features or getattr(settings, "ORB_MAX_FEATURES", 2000)
        self.min_matches = min_matches or getattr(settings, "MIN_MATCH_COUNT", 8)
        self.ransac_threshold = ransac_threshold or getattr(settings, "RANSAC_REPROJ_THRESHOLD", 5.0)

        # AI Segmentation configuration & models
        self.use_ai_segmentation = (
            use_ai_segmentation
            if use_ai_segmentation is not None
            else getattr(settings, "USE_AI_SEGMENTATION", True)
        )
        self.iou_threshold = (
            iou_threshold
            if iou_threshold is not None
            else getattr(settings, "REGION_IOU_THRESHOLD", 0.5)
        )

        self.sam_segmenter = sam_segmenter
        self.region_classifier = region_classifier
        self.reliability_engine = (
            reliability_engine if reliability_engine is not None else get_reliability_engine()
        )
        self.consensus_memory = (
            consensus_memory if consensus_memory is not None else get_consensus_memory()
        )

        # Initialize reusable ORB feature detector
        self.orb = cv2.ORB_create(
            nfeatures=self.max_orb_features,
            scaleFactor=1.2,
            nlevels=8,
            edgeThreshold=31,
            firstLevel=0,
            WTA_K=2,
            scoreType=cv2.ORB_HARRIS_SCORE,
            patchSize=31,
            fastThreshold=20,
        )

        # Initialize Brute-Force Matcher with Hamming distance for binary descriptors
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    # -------------------------------------------------------------------------
    # 1. Quality Assessment
    # -------------------------------------------------------------------------
    def assess_quality(self, image: np.ndarray) -> Dict[str, Any]:
        """Assess input photo quality across sharpness, exposure balance, and resolution.

        Algorithm:
            1. Sharpness / Blur: Computes the variance of the 64-bit float Laplacian
               operator over the grayscale image. Normalizes variance via a soft-saturation
               transfer function into [0.0, 1.0].
            2. Exposure / Glare: Measures the proportion of overexposed pixels (all channels > 240)
               and underexposed pixels (all channels < 15) using vectorized numpy masking.
            3. Resolution check: Compares (width, height) against minimum dimension limits.
            4. Composite Quality: Computes a weighted sum of sharpness, exposure, and
               resolution compliance, determining overall validity.

        Args:
            image: BGR, RGB, or Grayscale image array.

        Returns:
            Dict[str, Any]: Quality metrics including sharpness_score, exposure_score,
                resolution_ok, overall_quality_score, is_valid_quality, blur_score,
                glare_score, underexposure_score, resolution_w, and resolution_h.
        """
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            return {
                "sharpness_score": 0.0,
                "exposure_score": 0.0,
                "resolution_ok": False,
                "overall_quality_score": 0.0,
                "is_valid_quality": False,
                "blur_score": 0.0,
                "glare_score": 1.0,
                "underexposure_score": 0.0,
                "resolution_w": 0,
                "resolution_h": 0,
            }

        height, width = image.shape[:2]

        # 1. Blur evaluation via Laplacian variance
        laplacian_var = compute_laplacian_variance(image)
        sharpness_score = float(np.clip(laplacian_var / (laplacian_var + 120.0) * 1.5, 0.0, 1.0))

        # 2. Exposure evaluation (glare & underexposure)
        if len(image.shape) == 3 and image.shape[2] >= 3:
            glare_mask = np.all(image[:, :, :3] >= 240, axis=-1)
            under_mask = np.all(image[:, :, :3] <= 15, axis=-1)
        else:
            glare_mask = image >= 240
            under_mask = image <= 15

        total_pixels = float(image.shape[0] * image.shape[1])
        glare_ratio = float(np.count_nonzero(glare_mask) / total_pixels) if total_pixels > 0 else 0.0
        under_ratio = float(np.count_nonzero(under_mask) / total_pixels) if total_pixels > 0 else 0.0

        exposure_score = float(
            np.clip(1.0 - (glare_ratio * 2.2 + under_ratio * 1.5), 0.0, 1.0)
        )

        # 3. Resolution compliance
        resolution_ok = bool(width >= self.min_width and height >= self.min_height)
        res_factor = 1.0 if resolution_ok else max(
            0.2, (width * height) / float(self.min_width * self.min_height)
        )

        # 4. Composite quality metric
        overall_quality_score = float(
            np.clip(
                0.45 * sharpness_score + 0.40 * exposure_score + 0.15 * res_factor,
                0.0,
                1.0,
            )
        )

        is_valid_quality = bool(
            resolution_ok
            and laplacian_var >= self.min_blur_var
            and glare_ratio <= self.max_glare_ratio
            and overall_quality_score >= self.min_quality_threshold
        )

        return {
            "sharpness_score": round(sharpness_score, 4),
            "exposure_score": round(exposure_score, 4),
            "resolution_ok": resolution_ok,
            "overall_quality_score": round(overall_quality_score, 4),
            "is_valid_quality": is_valid_quality,
            "blur_score": round(laplacian_var, 4),
            "glare_score": round(glare_ratio, 4),
            "underexposure_score": round(under_ratio, 4),
            "resolution_w": int(width),
            "resolution_h": int(height),
        }

    def evaluate_quality(self, image: np.ndarray) -> Tuple[bool, float, float]:
        """Convenience alias for assess_quality returning (is_valid, blur_score, glare_score)."""
        metrics = self.assess_quality(image)
        return metrics["is_valid_quality"], metrics["blur_score"], metrics["glare_score"]

    # -------------------------------------------------------------------------
    # 2. EXIF Telemetry Extraction
    # -------------------------------------------------------------------------
    def extract_exif(
        self, image_input: Union[str, Path, bytes, BinaryIO, Image.Image]
    ) -> Dict[str, Any]:
        """Extract camera hardware, exposure settings, timestamp, and GPS telemetry from EXIF.

        Handles missing, partial, or stripped EXIF tags gracefully (e.g. from social media
        re-compression) without raising exceptions, returning None for absent fields.

        Args:
            image_input: File path, raw bytes buffer, or PIL Image object.

        Returns:
            Dict[str, Any]: Dictionary containing parsed EXIF fields.
        """
        exif_dict: Dict[str, Any] = {
            "camera_make": None,
            "camera_model": None,
            "iso": None,
            "exposure_time": None,
            "focal_length": None,
            "orientation": None,
            "gps_latitude": None,
            "gps_longitude": None,
            "gps_altitude": None,
            "timestamp": None,
        }

        try:
            pil_img = load_image_pil(image_input)
        except Exception as err:
            logger.warning(f"Could not open image for EXIF parsing: {err}")
            return exif_dict

        try:
            raw_exif = pil_img.getexif()
            if not raw_exif:
                return exif_dict

            # Decode standard EXIF tags
            for tag_id, value in raw_exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, tag_id)

                if tag_name == "Make" and isinstance(value, str):
                    exif_dict["camera_make"] = value.strip()
                elif tag_name == "Model" and isinstance(value, str):
                    exif_dict["camera_model"] = value.strip()
                elif tag_name == "Orientation" and isinstance(value, int):
                    exif_dict["orientation"] = value
                elif tag_name in ("DateTime", "DateTimeOriginal", "DateTimeDigitized"):
                    if not exif_dict["timestamp"] and isinstance(value, str):
                        exif_dict["timestamp"] = self._parse_exif_datetime(value)
                elif tag_name in ("ISOSpeedRatings", "PhotographicSensitivity"):
                    try:
                        exif_dict["iso"] = int(value)
                    except (ValueError, TypeError):
                        pass
                elif tag_name == "ExposureTime":
                    exif_dict["exposure_time"] = self._parse_float_or_rational(value)
                elif tag_name == "FocalLength":
                    exif_dict["focal_length"] = self._parse_float_or_rational(value)

            # Check IFD sub-exif if available for DateTimeOriginal / ISO / Lens
            try:
                exif_ifd = raw_exif.get_ifd(ExifTags.IFD.Exif)
                if exif_ifd:
                    for tag_id, value in exif_ifd.items():
                        tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                        if tag_name == "DateTimeOriginal" and isinstance(value, str):
                            exif_dict["timestamp"] = self._parse_exif_datetime(value)
                        elif tag_name == "ISOSpeedRatings" and exif_dict["iso"] is None:
                            try:
                                exif_dict["iso"] = int(value)
                            except (ValueError, TypeError):
                                pass
                        elif tag_name == "ExposureTime" and exif_dict["exposure_time"] is None:
                            exif_dict["exposure_time"] = self._parse_float_or_rational(value)
                        elif tag_name == "FocalLength" and exif_dict["focal_length"] is None:
                            exif_dict["focal_length"] = self._parse_float_or_rational(value)
            except Exception:
                pass

            # Extract GPS telemetry from GPSInfo IFD (tag 0x8825 / 34853)
            gps_info = None
            try:
                gps_info = raw_exif.get_ifd(ExifTags.IFD.GPSInfo)
            except Exception:
                pass

            if not gps_info:
                gps_info = raw_exif.get(34853)

            if gps_info and isinstance(gps_info, dict):
                lat, lon, alt = self._parse_gps_info(gps_info)
                exif_dict["gps_latitude"] = lat
                exif_dict["gps_longitude"] = lon
                exif_dict["gps_altitude"] = alt

        except Exception as err:
            logger.warning(f"Error during EXIF decoding: {err}")

        return exif_dict

    def extract_exif_schema(
        self, image_input: Union[str, Path, bytes, BinaryIO, Image.Image]
    ) -> EXIFMetadata:
        """Convenience method returning a validated Pydantic EXIFMetadata model."""
        raw_dict = self.extract_exif(image_input)
        return EXIFMetadata(**raw_dict)

    # -------------------------------------------------------------------------
    # 3. ORB Registration & Homography Alignment
    # -------------------------------------------------------------------------
    def register_image(
        self, image: np.ndarray, reference_image: np.ndarray
    ) -> Dict[str, Any]:
        """Register input photo against reference baseline photo using ORB and RANSAC homography.

        Args:
            image: Input query image array (BGR or Grayscale).
            reference_image: Reference baseline image array (BGR or Grayscale).

        Returns:
            Dict[str, Any]: Registration success status, homography matrix, and metrics.
        """
        fail_response: Dict[str, Any] = {
            "registration_success": False,
            "homography_matrix": None,
            "inlier_count": 0,
            "inlier_ratio": 0.0,
            "confidence_score": 0.0,
            "matched_keypoints_count": 0,
        }

        if (
            image is None
            or reference_image is None
            or not isinstance(image, np.ndarray)
            or not isinstance(reference_image, np.ndarray)
            or image.size == 0
            or reference_image.size == 0
        ):
            return fail_response

        # Convert to grayscale
        gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        gray_ref = (
            cv2.cvtColor(reference_image, cv2.COLOR_BGR2GRAY)
            if len(reference_image.shape) == 3
            else reference_image
        )

        # Detect ORB keypoints and descriptors
        kp_img, des_img = self.orb.detectAndCompute(gray_img, None)
        kp_ref, des_ref = self.orb.detectAndCompute(gray_ref, None)

        if (
            des_img is None
            or des_ref is None
            or len(kp_img) < 4
            or len(kp_ref) < 4
        ):
            return fail_response

        # Match descriptors via Hamming distance
        try:
            raw_matches = self.matcher.match(des_img, des_ref)
        except cv2.error as err:
            logger.warning(f"ORB Matcher error: {err}")
            return fail_response

        if not raw_matches:
            return fail_response

        # Sort matches by distance
        sorted_matches = sorted(raw_matches, key=lambda m: m.distance)

        # Keep top percentage of matches
        top_k = max(self.min_matches, int(len(sorted_matches) * 0.25))
        good_matches = sorted_matches[: min(len(sorted_matches), max(top_k, self.min_matches))]

        if len(good_matches) < self.min_matches:
            return fail_response

        # Extract coordinates of matched keypoints
        src_pts = np.float32([kp_img[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp_ref[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        # Compute Homography using RANSAC
        try:
            H_matrix, mask = cv2.findHomography(
                src_pts, dst_pts, cv2.RANSAC, self.ransac_threshold
            )
        except cv2.error as err:
            logger.warning(f"findHomography failed: {err}")
            return fail_response

        if H_matrix is None or mask is None:
            return fail_response

        inlier_count = int(np.sum(mask))
        inlier_ratio = float(inlier_count / len(good_matches)) if len(good_matches) > 0 else 0.0

        if inlier_count < 4 or inlier_ratio < 0.15:
            return {
                "registration_success": False,
                "homography_matrix": None,
                "inlier_count": inlier_count,
                "inlier_ratio": round(inlier_ratio, 4),
                "confidence_score": 0.0,
                "matched_keypoints_count": len(good_matches),
            }

        density_factor = min(1.0, inlier_count / 20.0)
        confidence_score = float(np.clip(inlier_ratio * (0.5 + 0.5 * density_factor), 0.0, 1.0))

        return {
            "registration_success": True,
            "homography_matrix": H_matrix,
            "inlier_count": inlier_count,
            "inlier_ratio": round(inlier_ratio, 4),
            "confidence_score": round(confidence_score, 4),
            "matched_keypoints_count": len(good_matches),
        }

    def match_and_register_region(
        self, image: np.ndarray, baseline_features: Dict[str, Any]
    ) -> Tuple[Optional[int], float, Optional[np.ndarray]]:
        """Match image against baseline features and return (region_id, confidence, homography)."""
        ref_image = baseline_features.get("reference_image")
        if ref_image is None:
            return None, 0.0, None

        res = self.register_image(image, ref_image)
        if res["registration_success"]:
            region_id = baseline_features.get("region_id", 1)
            return region_id, res["confidence_score"], res["homography_matrix"]
        return None, 0.0, None

    # -------------------------------------------------------------------------
    # 4. Sequential Prior Observation Query Helper
    # -------------------------------------------------------------------------
    def get_latest_observation(
        self, db: Session, region_id: Union[uuid.UUID, str]
    ) -> Optional[Observation]:
        """Fetch the most recently stored observation for an architectural region.

        Ordered by created_at desc, captured_at desc.
        Returns None if this is the first upload for the region (cold start).

        Args:
            db: Active SQLAlchemy database session.
            region_id: Architectural region UUID or string identifier.

        Returns:
            Optional[Observation]: Latest Observation ORM record or None.
        """
        region_uuid = self._resolve_uuid_or_none(region_id)
        if region_uuid is None or db is None:
            return None

        return (
            db.query(Observation)
            .filter(Observation.region_id == region_uuid)
            .order_by(Observation.created_at.desc(), Observation.captured_at.desc())
            .first()
        )

    # -------------------------------------------------------------------------
    # 5. Region Suggestion (AI-Assist without auto-commit)
    # -------------------------------------------------------------------------
    def suggest_region(
        self,
        image_bytes: bytes,
        monument_id: Union[uuid.UUID, str],
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Run SAM segmentation + OpenCLIP classification to suggest the most likely region.

        Returns the suggested region and the list of available existing regions for expert dropdown confirmation.
        Does NOT automatically commit a new region or observation to the database.

        Args:
            image_bytes: Raw bytes of uploaded photograph.
            monument_id: Monument UUID or identifier string.
            db: Optional database session to query existing regions.

        Returns:
            Dict[str, Any]: Structured dictionary conforming to RegionSuggestionResponse schema.
        """
        # 1. Decode image
        try:
            cv2_img = load_image_cv2(image_bytes)
        except Exception as err:
            logger.error(f"Failed to decode image bytes for region suggestion: {err}")
            raise ValueError(f"Invalid image format or corrupted bytes: {err}") from err

        # 2. Fetch existing regions for this monument from DB
        monument_uuid = self._resolve_monument_uuid(monument_id, db=db)
        existing_regions: List[Region] = []
        if db is not None:
            existing_regions = (
                db.query(Region)
                .filter(Region.monument_id == monument_uuid)
                .order_by(Region.name.asc())
                .all()
            )

        available_regions = [
            {
                "id": str(r.id),
                "name": r.name,
                "category": r.category,
                "bounding_box": r.bounding_box,
            }
            for r in existing_regions
        ]

        # 3. Run AI segmentation without persisting new rows to DB
        suggested_region_id: Optional[str] = None
        suggested_region_name: Optional[str] = None
        confidence_score: float = 0.0
        detected_category: Optional[str] = None
        bounding_box: Optional[List[int]] = None

        try:
            detected_regions = self.segment_regions(
                image=cv2_img,
                monument_id=str(monument_id),
                db=None,  # Do not auto-create region rows in suggestion pass
            )

            if detected_regions:
                # Select the highest confidence detected region
                best_detected = max(
                    detected_regions,
                    key=lambda r: r.get("confidence_score", 0.0),
                )
                detected_category = best_detected.get("category") or best_detected.get("region_type")
                bounding_box = best_detected.get("bbox")
                confidence_score = float(best_detected.get("confidence_score", 0.85))

                # Match against existing regions by IoU or Category
                best_match = None
                best_iou = 0.0
                for reg in existing_regions:
                    if (
                        reg.bounding_box
                        and isinstance(reg.bounding_box, (list, tuple))
                        and len(reg.bounding_box) >= 4
                        and bounding_box
                    ):
                        iou = self._compute_bbox_iou(bounding_box, reg.bounding_box[:4])
                        if reg.category == detected_category:
                            iou *= 1.2
                        if iou > best_iou:
                            best_iou = iou
                            best_match = reg
                    elif reg.category and detected_category and reg.category.lower() == detected_category.lower():
                        if best_match is None:
                            best_match = reg

                if best_match is not None:
                    suggested_region_id = str(best_match.id)
                    suggested_region_name = best_match.name
                else:
                    if existing_regions:
                        suggested_region_id = str(existing_regions[0].id)
                        suggested_region_name = existing_regions[0].name
                    else:
                        suggested_region_name = best_detected.get("name") or detected_category
        except Exception as seg_err:
            logger.warning(f"Error during AI region suggestion pass: {seg_err}")
            if existing_regions:
                suggested_region_id = str(existing_regions[0].id)
                suggested_region_name = existing_regions[0].name
                confidence_score = 0.5

        return {
            "monument_id": str(monument_id),
            "suggested_region_id": suggested_region_id,
            "suggested_region_name": suggested_region_name,
            "confidence_score": round(confidence_score, 4),
            "detected_category": detected_category,
            "bounding_box": bounding_box,
            "available_regions": available_regions,
        }

    # -------------------------------------------------------------------------
    # 6. Region Segmentation & IoU DB Resolution (SAM + CLIP + Fallback)
    # -------------------------------------------------------------------------
    @staticmethod
    def _compute_bbox_iou(
        box_a: Union[List[Union[int, float]], Tuple[Union[int, float], ...]],
        box_b: Union[List[Union[int, float]], Tuple[Union[int, float], ...]],
    ) -> float:
        """Compute Intersection-over-Union (IoU) between two bounding boxes [x, y, w, h]."""
        if len(box_a) < 4 or len(box_b) < 4:
            return 0.0

        xa, ya, wa, ha = box_a[:4]
        xb, yb, wb, hb = box_b[:4]

        xa1, ya1, xa2, ya2 = xa, ya, xa + wa, ya + ha
        xb1, yb1, xb2, yb2 = xb, yb, xb + wb, yb + hb

        inter_x1 = max(xa1, xb1)
        inter_y1 = max(ya1, yb1)
        inter_x2 = min(xa2, xb2)
        inter_y2 = min(ya2, yb2)

        inter_w = max(0.0, inter_x2 - inter_x1)
        inter_h = max(0.0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h

        area_a = max(0.0, wa * ha)
        area_b = max(0.0, wb * hb)
        union_area = area_a + area_b - inter_area

        if union_area <= 0.0:
            return 0.0

        return float(inter_area / union_area)

    @staticmethod
    def _resolve_uuid_or_none(val: Any) -> Optional[uuid.UUID]:
        """Safely convert value to UUID or return None."""
        if val is None:
            return None
        if isinstance(val, uuid.UUID):
            return val
        try:
            return uuid.UUID(str(val))
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _resolve_monument_uuid(monument_id: Union[uuid.UUID, str], db: Optional[Session] = None) -> uuid.UUID:
        """Resolve or generate a UUID for a monument identifier and ensure record exists in DB."""
        if isinstance(monument_id, uuid.UUID):
            mon_uuid = monument_id
        else:
            try:
                mon_uuid = uuid.UUID(str(monument_id))
            except (ValueError, AttributeError):
                mon_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, str(monument_id))

        if db is not None:
            from app.models.monument import Monument
            monument = db.query(Monument).filter(Monument.id == mon_uuid).first()
            if not monument:
                monument = Monument(
                    id=mon_uuid,
                    name=str(monument_id),
                    location_name="Monitored Site",
                    heritage_status="Registered",
                    importance_tier=1,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(monument)
                db.commit()
                db.refresh(monument)
        return mon_uuid

    def _resolve_or_create_region(
        self,
        db: Session,
        monument_id: Union[uuid.UUID, str],
        region_type: str,
        bbox: List[int],
        polygon: Optional[List[List[float]]] = None,
    ) -> Union[uuid.UUID, int, str]:
        """Resolve region_id against existing monument Region rows via IoU, or insert a new record."""
        monument_uuid = self._resolve_monument_uuid(monument_id, db=db)
        existing_regions = db.query(Region).filter_by(monument_id=monument_uuid).all()

        best_match = None
        best_iou = 0.0

        for reg in existing_regions:
            if (
                reg.bounding_box
                and isinstance(reg.bounding_box, (list, tuple))
                and len(reg.bounding_box) >= 4
            ):
                iou = self._compute_bbox_iou(bbox, reg.bounding_box[:4])
                if reg.category == region_type:
                    iou *= 1.1

                if iou > best_iou:
                    best_iou = iou
                    best_match = reg

        if best_match is not None and best_iou >= self.iou_threshold:
            logger.debug(
                f"Matched existing Region ID {best_match.id} ('{best_match.name}') with IoU {best_iou:.3f}"
            )
            return best_match.id

        cat_count = sum(1 for r in existing_regions if r.category == region_type)
        reg_name = f"{region_type.replace(' ', '_')}_{cat_count + 1}"

        new_reg = Region(
            monument_id=monument_uuid,
            name=reg_name,
            category=region_type,
            bounding_box=bbox,
            reference_features={"polygon": polygon} if polygon else None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(new_reg)
        db.commit()
        db.refresh(new_reg)
        logger.info(
            f"Created new Region record ID {new_reg.id} ('{reg_name}') for monument '{monument_id}'"
        )
        return new_reg.id

    def _segment_regions_homography_fallback(
        self,
        image: np.ndarray,
        homography_matrix: Optional[np.ndarray] = None,
        reference_regions: Optional[List[Dict[str, Any]]] = None,
        monument_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """Fallback method: project reference regions onto query image via inverse homography."""
        if image is None or image.size == 0:
            return []

        img_h, img_w = image.shape[:2]

        if not reference_regions:
            reference_regions = [
                {
                    "region_id": 1,
                    "name": "central_facade",
                    "category": "facade",
                    "bounding_box": [
                        int(img_w * 0.2),
                        int(img_h * 0.2),
                        int(img_w * 0.6),
                        int(img_h * 0.6),
                    ],
                }
            ]

        H_inv = None
        if homography_matrix is not None:
            try:
                ret, H_inv = cv2.invert(homography_matrix)
                if not ret:
                    H_inv = None
            except cv2.error:
                H_inv = None

        projected_regions: List[Dict[str, Any]] = []

        for reg in reference_regions:
            raw_id = reg.get("id") or reg.get("region_id", 1)
            name = reg.get("name", f"region_{raw_id}")
            category = reg.get("category", "architectural_component")
            raw_bbox = reg.get("bounding_box") or [0, 0, img_w, img_h]

            rx, ry, rw, rh = raw_bbox[:4]

            if H_inv is not None:
                corners = np.array(
                    [
                        [[rx, ry]],
                        [[rx + rw, ry]],
                        [[rx + rw, ry + rh]],
                        [[rx, ry + rh]],
                    ],
                    dtype=np.float32,
                )
                try:
                    projected_pts = cv2.perspectiveTransform(corners, H_inv)
                    min_x = max(0.0, float(np.min(projected_pts[:, 0, 0])))
                    min_y = max(0.0, float(np.min(projected_pts[:, 0, 1])))
                    max_x = min(float(img_w), float(np.max(projected_pts[:, 0, 0])))
                    max_y = min(float(img_h), float(np.max(projected_pts[:, 0, 1])))

                    proj_w = max(0.0, max_x - min_x)
                    proj_h = max(0.0, max_y - min_y)
                    bbox = [int(round(min_x)), int(round(min_y)), int(round(proj_w)), int(round(proj_h))]
                    polygon = [
                        [round(float(p[0][0]), 1), round(float(p[0][1]), 1)]
                        for p in projected_pts
                    ]
                except Exception as err:
                    logger.warning(f"Perspective transform error on region {raw_id}: {err}")
                    bbox = [int(rx), int(ry), int(rw), int(rh)]
                    polygon = []
            else:
                bbox = [int(rx), int(ry), int(rw), int(rh)]
                polygon = []

            # Resolve in DB if session available
            if db is not None and monument_id is not None:
                resolved_id = self._resolve_or_create_region(
                    db=db,
                    monument_id=monument_id,
                    region_type=category,
                    bbox=bbox,
                    polygon=polygon,
                )
            else:
                resolved_id = raw_id

            projected_regions.append(
                {
                    "region_id": resolved_id,
                    "name": name,
                    "category": category,
                    "region_type": category,
                    "bbox": bbox,
                    "polygon": polygon,
                }
            )

        return projected_regions

    def segment_regions(
        self,
        image: np.ndarray,
        monument_id: Optional[str] = None,
        db: Optional[Session] = None,
        homography_matrix: Optional[np.ndarray] = None,
        reference_regions: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Segment architectural components via SAM + OpenCLIP with DB resolution and homography fallback."""
        if image is None or image.size == 0:
            return []

        if self.use_ai_segmentation:
            try:
                if self.sam_segmenter is None:
                    self.sam_segmenter = get_sam_segmenter()
                if self.region_classifier is None:
                    self.region_classifier = get_region_classifier()

                masks = self.sam_segmenter.generate_masks(image)
                if not masks:
                    logger.warning(
                        "SAM generated 0 masks. Falling back to homography-based projection."
                    )
                    return self._segment_regions_homography_fallback(
                        image=image,
                        homography_matrix=homography_matrix,
                        reference_regions=reference_regions,
                        monument_id=monument_id,
                        db=db,
                    )

                classified_masks = self.region_classifier.classify_masks(
                    image=image,
                    masks=masks,
                    sam_segmenter=self.sam_segmenter,
                )

                if not classified_masks:
                    logger.warning(
                        "All SAM masks were classified as non-structural/negative objects. "
                        "Returning empty regions list."
                    )
                    return []

                result_regions: List[Dict[str, Any]] = []
                for idx, item in enumerate(classified_masks):
                    bbox = item["bbox"]
                    region_type = item["region_type"]
                    conf = item.get("confidence_score", 1.0)
                    all_scores = item.get("all_scores", {})

                    if db is not None and monument_id is not None:
                        region_id = self._resolve_or_create_region(
                            db=db,
                            monument_id=monument_id,
                            region_type=region_type,
                            bbox=bbox,
                        )
                    else:
                        region_id = idx + 1

                    result_regions.append(
                        {
                            "region_id": region_id,
                            "name": f"{region_type}_{region_id}",
                            "category": region_type,
                            "region_type": region_type,
                            "bbox": bbox,
                            "confidence_score": conf,
                            "all_scores": all_scores,
                        }
                    )

                return result_regions

            except Exception as ai_err:
                logger.warning(
                    f"AI segmentation failed with error: {ai_err}. "
                    "Falling back to homography-based projection."
                )
                return self._segment_regions_homography_fallback(
                    image=image,
                    homography_matrix=homography_matrix,
                    reference_regions=reference_regions,
                    monument_id=monument_id,
                    db=db,
                )

        return self._segment_regions_homography_fallback(
            image=image,
            homography_matrix=homography_matrix,
            reference_regions=reference_regions,
            monument_id=monument_id,
            db=db,
        )

    # -------------------------------------------------------------------------
    # 7. Full Pipeline Orchestration (Expert Ingestion Flow)
    # -------------------------------------------------------------------------
    def ingest(
        self,
        image_bytes: bytes,
        monument_id: str,
        region_id: Optional[Union[uuid.UUID, str]] = None,
        reference_image: Optional[np.ndarray] = None,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
        reference_regions: Optional[List[Dict[str, Any]]] = None,
        image_url: Optional[str] = None,
        auto_score_reliability: bool = True,
        auto_update_consensus: bool = True,
    ) -> ImageIngestionResponse:
        """Execute Module 1 ingestion pipeline for an expert-confirmed monument photograph.

        Orchestrates:
            1. Image decoding & quality assessment (blur Laplacian variance, glare/exposure ratio).
            2. EXIF metadata extraction (camera, GPS, timestamp).
            3. Explicit region assignment or fallback matching.
            4. Sequential alignment against the MOST RECENTLY STORED observation for the region
               (cold start marks pristine baseline with registration_success=True).
            5. Disk persistence for sequential alignment history.
            6. Appending observation record to historical sequence in PostgreSQL.

        Args:
            image_bytes: Raw bytes of uploaded photograph.
            monument_id: Unique monument identifier string or UUID.
            region_id: Explicit region identifier confirmed by expert.
            reference_image: Optional manual reference baseline image array.
            user_id: Optional expert contributor identifier.
            db: Optional database session for persistence and latest observation lookup.
            reference_regions: Optional fallback region definitions.
            image_url: Optional remote or local image path.
            auto_score_reliability: Flag to toggle legacy reliability scoring (default: False).
            auto_update_consensus: Flag to toggle legacy consensus memory update (default: False).

        Returns:
            ImageIngestionResponse: Standardized response schema with quality scores,
                EXIF metadata, matched region ID, registration confidence, and baseline indicator.
        """
        # 1. Decode image bytes
        try:
            cv2_img = load_image_cv2(image_bytes)
        except Exception as err:
            logger.error(f"Failed to decode image bytes: {err}")
            raise ValueError(f"Invalid image format or corrupted bytes: {err}") from err

        # 2. Quality assessment
        quality = self.assess_quality(cv2_img)

        # 3. EXIF extraction
        exif_dict = self.extract_exif(image_bytes)
        exif_schema = EXIFMetadata(**exif_dict)

        # 4. Resolve Target Region ID
        matched_region_id: Optional[Union[uuid.UUID, int, str]] = None
        if region_id is not None:
            resolved_reg_uuid = self._resolve_uuid_or_none(region_id)
            if db is not None:
                monument_uuid = self._resolve_monument_uuid(monument_id, db=db)
                if resolved_reg_uuid is not None:
                    db_region = db.query(Region).filter(Region.id == resolved_reg_uuid).first()
                    if not db_region:
                        db_region = Region(
                            id=resolved_reg_uuid,
                            monument_id=monument_uuid,
                            name=f"Region_{str(resolved_reg_uuid)[:8]}",
                            category="architectural_component",
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        )
                        db.add(db_region)
                        db.commit()
                        db.refresh(db_region)
                    matched_region_id = db_region.id
                else:
                    db_region = db.query(Region).filter(Region.monument_id == monument_uuid, Region.name == str(region_id)).first()
                    if not db_region:
                        db_region = Region(
                            monument_id=monument_uuid,
                            name=str(region_id),
                            category="architectural_component",
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        )
                        db.add(db_region)
                        db.commit()
                        db.refresh(db_region)
                    matched_region_id = db_region.id
            else:
                matched_region_id = resolved_reg_uuid or region_id
        elif quality["is_valid_quality"]:
            # Fallback if no explicit region provided: run segmentation
            try:
                regions = self.segment_regions(
                    image=cv2_img,
                    monument_id=monument_id,
                    db=db,
                    reference_regions=reference_regions,
                )
                if regions:
                    matched_region_id = regions[0]["region_id"]
            except Exception as seg_err:
                logger.error(f"Error during fallback region segmentation: {seg_err}")
                matched_region_id = None

        # 5. Alignment against Most Recent Observation (Sequential Alignment)
        is_baseline: bool = False
        registration_success: bool = False
        registration_confidence: Optional[float] = None
        homography_matrix: Optional[np.ndarray] = None

        prior_obs = None
        if db is not None and matched_region_id is not None:
            prior_obs = self.get_latest_observation(db=db, region_id=matched_region_id)

        if reference_image is not None:
            # Explicit reference image provided
            reg_res = self.register_image(cv2_img, reference_image)
            registration_success = reg_res["registration_success"]
            registration_confidence = reg_res["confidence_score"]
            homography_matrix = reg_res["homography_matrix"]
            is_baseline = False
        elif prior_obs is not None:
            # Align against most recent prior observation image for this region
            ref_cv2 = None
            if prior_obs.image_url:
                candidate_paths = [
                    prior_obs.image_url,
                    os.path.join(getattr(settings, "UPLOAD_DIR", "./uploads"), os.path.basename(prior_obs.image_url)),
                ]
                for p in candidate_paths:
                    if os.path.exists(p):
                        try:
                            ref_cv2 = cv2.imread(p)
                            if ref_cv2 is not None:
                                break
                        except Exception:
                            pass

            if ref_cv2 is not None:
                reg_res = self.register_image(cv2_img, ref_cv2)
                registration_success = reg_res["registration_success"]
                registration_confidence = reg_res["confidence_score"]
                homography_matrix = reg_res["homography_matrix"]
            else:
                registration_success = False
                registration_confidence = 0.0
            is_baseline = False
        else:
            # Cold start: first upload for this region (baseline photo)
            is_baseline = True
            registration_success = True
            registration_confidence = 1.0
            homography_matrix = None

        # 6. Save Image to Local Storage
        upload_dir_str = getattr(settings, "UPLOAD_DIR", "./uploads")
        os.makedirs(upload_dir_str, exist_ok=True)
        saved_filename = f"{monument_id}_{matched_region_id or 'general'}_{uuid.uuid4().hex[:8]}.jpg"
        disk_filepath = os.path.join(upload_dir_str, saved_filename).replace("\\", "/")
        try:
            with open(disk_filepath, "wb") as f_out:
                f_out.write(image_bytes)
            resolved_image_url = disk_filepath
        except Exception as save_err:
            logger.warning(f"Failed to write image to disk at {disk_filepath}: {save_err}")
            resolved_image_url = disk_filepath

        captured_timestamp = exif_dict.get("timestamp") or datetime.now(timezone.utc)

        # 7. Database Persistence
        observation_id = uuid.uuid4()
        if db is not None:
            try:
                monument_uuid = self._resolve_monument_uuid(monument_id, db=db)
                exif_json_safe = {
                    k: v.isoformat() if isinstance(v, datetime) else v
                    for k, v in exif_dict.items()
                }

                obs_record = Observation(
                    monument_id=monument_uuid,
                    user_id=user_id,
                    image_url=resolved_image_url,
                    blur_score=quality.get("blur_score"),
                    sharpness_score=quality.get("sharpness_score"),
                    glare_score=quality.get("glare_score"),
                    exposure_score=quality.get("exposure_score"),
                    overall_quality_score=quality.get("overall_quality_score"),
                    is_valid_quality=quality.get("is_valid_quality", True),
                    resolution_width=quality.get("resolution_w"),
                    resolution_height=quality.get("resolution_h"),
                    exif_data=exif_json_safe,
                    registration_success=registration_success,
                    registration_confidence=registration_confidence,
                    reliability_score=quality.get("overall_quality_score"),
                    region_id=self._resolve_uuid_or_none(matched_region_id),
                    captured_at=captured_timestamp,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(obs_record)
                db.commit()
                db.refresh(obs_record)
                observation_id = obs_record.id

                # Optional legacy hooks (disabled by default in expert flow)
                if auto_score_reliability and self.reliability_engine is not None:
                    try:
                        self.reliability_engine.compute_reliability(obs_record, db=db)
                    except Exception as rel_err:
                        logger.warning(f"Reliability computation error: {rel_err}")

                if auto_update_consensus and self.consensus_memory is not None:
                    if obs_record.region_id is not None:
                        try:
                            self.consensus_memory.process_observation(obs_record, db=db, image=cv2_img)
                        except Exception as cons_err:
                            logger.warning(f"Consensus memory update error: {cons_err}")

            except Exception as err:
                db.rollback()
                logger.error(f"Database error saving observation: {err}")
                raise

        return ImageIngestionResponse(
            observation_id=observation_id,
            monument_id=monument_id,
            is_valid_quality=quality["is_valid_quality"],
            blur_score=quality["blur_score"],
            glare_score=quality["glare_score"],
            resolution_w=quality["resolution_w"],
            resolution_h=quality["resolution_h"],
            exif=exif_schema,
            matched_region_id=matched_region_id,
            registration_success=registration_success,
            registration_confidence=registration_confidence,
            is_baseline=is_baseline,
            created_at=datetime.now(timezone.utc),
        )

    # -------------------------------------------------------------------------
    # Helper Parsing Utilities
    # -------------------------------------------------------------------------
    @staticmethod
    def _parse_exif_datetime(dt_str: str) -> Optional[datetime]:
        """Parse EXIF timestamp string into Python datetime object."""
        if not dt_str or not isinstance(dt_str, str):
            return None
        dt_str = dt_str.strip()
        for fmt in (
            "%Y:%m:%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y:%m:%d %H:%M:%S%z",
            "%Y/%m/%d %H:%M:%S",
        ):
            try:
                return datetime.strptime(dt_str[:19], fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_float_or_rational(value: Any) -> Optional[float]:
        """Safely parse float, int, or IFDRational/tuple into a Python float."""
        if value is None:
            return None
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if hasattr(value, "numerator") and hasattr(value, "denominator"):
                return float(value.numerator) / float(value.denominator) if value.denominator != 0 else 0.0
            if isinstance(value, (tuple, list)) and len(value) == 2:
                num, den = value
                return float(num) / float(den) if den != 0 else 0.0
            return float(value)
        except Exception:
            return None

    @classmethod
    def _parse_gps_info(
        cls, gps_data: Dict[Any, Any]
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Parse EXIF GPSInfo tags and convert DMS coordinates to decimal degrees."""
        named_gps: Dict[str, Any] = {}
        for key, val in gps_data.items():
            tag_name = ExifTags.GPSTAGS.get(key, key)
            named_gps[tag_name] = val

        lat = cls._convert_dms_to_decimal(
            named_gps.get("GPSLatitude"), named_gps.get("GPSLatitudeRef", "N")
        )
        lon = cls._convert_dms_to_decimal(
            named_gps.get("GPSLongitude"), named_gps.get("GPSLongitudeRef", "E")
        )

        alt = cls._parse_float_or_rational(named_gps.get("GPSAltitude"))
        alt_ref = named_gps.get("GPSAltitudeRef", 0)
        if alt is not None and alt_ref == 1:
            alt = -alt

        return lat, lon, alt

    @classmethod
    def _convert_dms_to_decimal(cls, dms: Any, ref: Optional[str]) -> Optional[float]:
        """Convert DMS (degrees, minutes, seconds) tuple to signed decimal degrees."""
        if not dms or not isinstance(dms, (tuple, list)) or len(dms) < 3:
            return None

        try:
            deg = cls._parse_float_or_rational(dms[0])
            mins = cls._parse_float_or_rational(dms[1])
            sec = cls._parse_float_or_rational(dms[2])

            if deg is None or mins is None or sec is None:
                return None

            decimal = deg + (mins / 60.0) + (sec / 3600.0)
            if ref and str(ref).upper() in ("S", "W"):
                decimal = -decimal
            return round(decimal, 6)
        except Exception:
            return None
