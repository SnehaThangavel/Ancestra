"""Module 1: Image Quality Assessment, EXIF Metadata Extraction, and ORB Registration.

SESCI Architecture - Patent Claim Scope:
Handles image quality validation (Laplacian variance blur, luminance glare/exposure),
EXIF telemetry parsing (DMS-to-decimal GPS, timestamp, camera make/model),
ORB keypoint feature matching, and RANSAC homography alignment against baseline
architectural monument regions.
"""

from typing import Dict, Any, Tuple, Optional, List, Union, BinaryIO
import io
import uuid
from datetime import datetime, timezone
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ExifTags
from sqlalchemy.orm import Session

from app.config import settings
from app.models.observation import Observation
from app.schemas.ingestion import EXIFMetadata, ImageIngestionResponse
from app.utils.image_utils import (
    compute_laplacian_variance,
    detect_glare_ratio,
    load_image_cv2,
    load_image_pil,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ImageIngestionModule:
    """Production-grade implementation of Module 1: Image Ingestion & Registration."""

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
    ) -> None:
        """Initialize the Image Ingestion module with configurable thresholds.

        Args:
            min_width: Minimum allowable image width in pixels.
            min_height: Minimum allowable image height in pixels.
            min_blur_var: Minimum Laplacian variance for sharpness acceptable threshold.
            max_glare_ratio: Maximum fraction of glare/saturated pixels before rejection.
            min_quality_threshold: Minimum overall composite quality score [0, 1].
            max_orb_features: Number of ORB features to compute for keypoint matching.
            min_matches: Minimum number of matched keypoints required for homography estimation.
            ransac_threshold: Maximum allowable reprojection error in pixels for RANSAC.
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
        # Smooth normalized sharpness score: 0.0 (fully blurred) to 1.0 (crisp edge contrast)
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
            Dict[str, Any]: Dictionary containing parsed EXIF fields:
                - camera_make (str or None)
                - camera_model (str or None)
                - iso (int or None)
                - exposure_time (float or None)
                - focal_length (float or None)
                - orientation (int or None)
                - gps_latitude (float decimal degrees or None)
                - gps_longitude (float decimal degrees or None)
                - gps_altitude (float meters or None)
                - timestamp (datetime or None)
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
                # Fallback to direct tag lookup
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
        """Register input photo against reference monument image using ORB and RANSAC homography.

        Algorithm:
            1. Converts input and reference images to single-channel 8-bit grayscale.
            2. Detects keypoints and extracts binary descriptors with ORB (up to max_orb_features).
            3. Matches descriptors using Brute-Force Matcher with Hamming norm & cross-checking.
            4. Sorts matches by Hamming distance and keeps top candidates.
            5. Computes perspective homography matrix using RANSAC to reject outlier matches.
            6. Calculates inlier ratio and composite registration confidence score.
            7. If insufficient matches (< min_matches) or poor inlier ratio, gracefully returns
               registration_success=False with None homography.

        Args:
            image: Input query image array (BGR or Grayscale).
            reference_image: Reference monument baseline image array (BGR or Grayscale).

        Returns:
            Dict[str, Any]:
                - registration_success (bool): True if robust homography was found.
                - homography_matrix (np.ndarray or None): 3x3 perspective transform matrix.
                - inlier_count (int): Number of RANSAC inlier matches.
                - inlier_ratio (float): Fraction of matches that are inliers.
                - confidence_score (float): Normalized alignment confidence [0.0, 1.0].
                - matched_keypoints_count (int): Total good matches evaluated.
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

        # Keep top percentage of matches (at least min_matches if available)
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

        # Minimum inliers required for a valid perspective registration
        if inlier_count < 4 or inlier_ratio < 0.15:
            return {
                "registration_success": False,
                "homography_matrix": None,
                "inlier_count": inlier_count,
                "inlier_ratio": round(inlier_ratio, 4),
                "confidence_score": 0.0,
                "matched_keypoints_count": len(good_matches),
            }

        # Calculate confidence metric scaling by both inlier ratio and absolute inlier density
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
    # 4. Region Segmentation & Projection
    # -------------------------------------------------------------------------
    def segment_regions(
        self,
        image: np.ndarray,
        homography_matrix: Optional[np.ndarray] = None,
        reference_regions: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Segment architectural components and project reference regions onto query image.

        # TODO: Upgrade to SAM (Segment Anything Model) + OpenCLIP zero-shot segmentation
        # (Module AI Upgrade in app/ai/sam_segmenter.py & app/ai/region_classifier.py).

        Current homography-projection baseline:
            Projects predefined reference bounding boxes (pillar, arch, facade, dome, frieze)
            from reference monument space into query image coordinate space using the inverse
            homography transformation matrix.

        Args:
            image: Query image array.
            homography_matrix: 3x3 homography mapping query image -> reference image.
            reference_regions: Optional list of architectural region definitions.

        Returns:
            List[Dict[str, Any]]: List of projected regions with region_id, name,
                category, bbox [x, y, w, h], and polygon coordinates.
        """
        if image is None or image.size == 0:
            return []

        img_h, img_w = image.shape[:2]

        if not reference_regions:
            # Default architectural reference zones for monument if not provided
            reference_regions = [
                {
                    "region_id": 1,
                    "name": "central_facade",
                    "category": "facade",
                    "bounding_box": [int(img_w * 0.2), int(img_h * 0.2), int(img_w * 0.6), int(img_h * 0.6)],
                }
            ]

        # Invert homography to project reference coords -> query image coords
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
            r_id = reg.get("id") or reg.get("region_id", 1)
            name = reg.get("name", f"region_{r_id}")
            category = reg.get("category", "architectural_component")
            raw_bbox = reg.get("bounding_box") or [0, 0, img_w, img_h]

            rx, ry, rw, rh = raw_bbox[:4]

            if H_inv is not None:
                # 4 corners in reference space
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
                    bbox = [round(min_x, 1), round(min_y, 1), round(proj_w, 1), round(proj_h, 1)]
                    polygon = [[round(float(p[0][0]), 1), round(float(p[0][1]), 1)] for p in projected_pts]
                except Exception as err:
                    logger.warning(f"Perspective transform error on region {r_id}: {err}")
                    bbox = [float(rx), float(ry), float(rw), float(rh)]
                    polygon = []
            else:
                bbox = [float(rx), float(ry), float(rw), float(rh)]
                polygon = []

            projected_regions.append(
                {
                    "region_id": r_id,
                    "name": name,
                    "category": category,
                    "bbox": bbox,
                    "polygon": polygon,
                }
            )

        return projected_regions

    # -------------------------------------------------------------------------
    # 5. Full Pipeline Orchestration (Ingest)
    # -------------------------------------------------------------------------
    def ingest(
        self,
        image_bytes: bytes,
        monument_id: str,
        reference_image: Optional[np.ndarray] = None,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
        reference_regions: Optional[List[Dict[str, Any]]] = None,
        image_url: Optional[str] = None,
    ) -> ImageIngestionResponse:
        """Execute end-to-end Module 1 ingestion pipeline for a crowdsourced photo.

        Orchestrates:
            1. Image decoding & validation.
            2. Quality assessment (sharpness, glare, resolution).
            3. EXIF metadata extraction (GPS, timestamp, hardware).
            4. ORB keypoint matching & RANSAC homography registration.
            5. Architectural region segmentation projection.
            6. Database persistence into Observation ORM record.

        Args:
            image_bytes: Raw bytes of uploaded photograph.
            monument_id: Unique monument string identifier.
            reference_image: Optional reference baseline image array for registration.
            user_id: Optional contributor user ID.
            db: Optional SQLAlchemy database session for persistence.
            reference_regions: Optional architectural region templates.
            image_url: Optional remote or local URL for the stored photo.

        Returns:
            ImageIngestionResponse: Standardized SESCI response schema with quality scores,
                EXIF metadata, matched region ID, and registration confidence.
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

        # 4. Registration & segmentation
        matched_region_id: Optional[int] = None
        registration_confidence: Optional[float] = None
        homography_matrix: Optional[np.ndarray] = None

        if reference_image is not None and quality["is_valid_quality"]:
            reg_res = self.register_image(cv2_img, reference_image)
            if reg_res["registration_success"]:
                homography_matrix = reg_res["homography_matrix"]
                registration_confidence = reg_res["confidence_score"]
                regions = self.segment_regions(
                    cv2_img,
                    homography_matrix=homography_matrix,
                    reference_regions=reference_regions,
                )
                if regions:
                    matched_region_id = regions[0]["region_id"]

        # Default fallback image URL
        resolved_image_url = image_url or f"uploads/{monument_id}_{uuid.uuid4().hex[:8]}.jpg"
        captured_timestamp = exif_dict.get("timestamp") or datetime.now(timezone.utc)

        # 5. Database Persistence
        observation_id = 1
        if db is not None:
            try:
                # Prepare JSON-safe serialization of exif_dict
                exif_json_safe = {
                    k: v.isoformat() if isinstance(v, datetime) else v
                    for k, v in exif_dict.items()
                }
                obs_record = Observation(
                    monument_id=monument_id,
                    user_id=user_id,
                    image_url=resolved_image_url,
                    blur_score=quality["blur_score"],
                    glare_score=quality["glare_score"],
                    resolution_w=quality["resolution_w"],
                    resolution_h=quality["resolution_h"],
                    exif_metadata=exif_json_safe,
                    reliability_score=quality["overall_quality_score"],
                    region_id=matched_region_id,
                    captured_at=captured_timestamp,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(obs_record)
                db.commit()
                db.refresh(obs_record)
                observation_id = obs_record.id
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
            registration_confidence=registration_confidence,
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
        # Map numeric IDs to names if needed
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
