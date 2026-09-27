"""Tests for Module 1 (Image Ingestion, Quality Assessment, & AI Region Segmentation)."""

from unittest.mock import MagicMock
import io
import uuid
import datetime
import pytest
import numpy as np
import cv2
from PIL import Image, ExifTags
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.modules.ingestion import ImageIngestionModule
from app.models.observation import Observation
from app.models.region import Region
from app.ai.sam_segmenter import SAMSegmenter
from app.ai.region_classifier import CLIPRegionClassifier


@pytest.fixture
def ingestion_module() -> ImageIngestionModule:
    """Fixture providing initialized ImageIngestionModule."""
    return ImageIngestionModule(
        min_width=400,
        min_height=300,
        min_blur_var=80.0,
        max_glare_ratio=0.25,
        min_quality_threshold=0.35,
        use_ai_segmentation=False,  # default to fallback in basic unit tests
    )




def _generate_synthetic_monument_image(width=600, height=450, blur=False, glare=False) -> np.ndarray:
    """Helper to generate textured synthetic architectural images with geometric features."""
    img = np.zeros((height, width, 3), dtype=np.uint8)

    # Base stone wall gradient
    for y in range(height):
        intensity = int(120 + 40 * np.sin(y / 30.0))
        img[y, :, :] = intensity

    # Add high-contrast architectural features (arch, columns, frieze)
    # Column 1
    cv2.rectangle(img, (int(width * 0.15), int(height * 0.3)), (int(width * 0.25), int(height * 0.9)), (60, 60, 60), -1)
    # Column 2
    cv2.rectangle(img, (int(width * 0.75), int(height * 0.3)), (int(width * 0.85), int(height * 0.9)), (60, 60, 60), -1)
    # Central arch
    cv2.ellipse(img, (int(width * 0.5), int(height * 0.45)), (int(width * 0.2), int(height * 0.25)), 0, 180, 360, (40, 40, 40), -1)
    # Cornice frieze pattern
    for x in range(0, width, 30):
        cv2.circle(img, (x + 15, int(height * 0.2)), 8, (220, 220, 220), -1)
        cv2.rectangle(img, (x, int(height * 0.22)), (x + 25, int(height * 0.26)), (70, 70, 70), -1)

    if glare:
        img[int(height * 0.1) : int(height * 0.6), int(width * 0.2) : int(width * 0.8)] = 252

    if blur:
        img = cv2.GaussianBlur(img, (61, 61), 0)

    return img


def _create_image_bytes_with_exif(img_arr: np.ndarray, include_exif: bool = True) -> bytes:
    """Encode OpenCV BGR image array to JPEG bytes with optional simulated EXIF."""
    rgb = cv2.cvtColor(img_arr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)

    if not include_exif:
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

    exif = pil_img.getexif()
    exif[271] = "Canon"
    exif[272] = "EOS 5D Mark IV"
    exif[274] = 1
    exif[306] = "2026:05:14 10:30:00"

    gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
    gps_ifd[1] = "N"
    gps_ifd[2] = (12.0, 58.0, 45.50)
    gps_ifd[3] = "E"
    gps_ifd[4] = (77.0, 34.0, 22.80)
    gps_ifd[5] = 0
    gps_ifd[6] = 920.0
    exif[34853] = gps_ifd

    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=90, exif=exif)
    return buf.getvalue()


# -----------------------------------------------------------------------------
# Unit Tests
# -----------------------------------------------------------------------------

def test_assess_quality_normal_clear_photo(ingestion_module) -> None:
    """Test quality assessment on a clear, high-contrast monument photo."""
    img = _generate_synthetic_monument_image(width=640, height=480, blur=False, glare=False)
    metrics = ingestion_module.assess_quality(img)

    assert metrics["resolution_ok"] is True
    assert metrics["blur_score"] > ingestion_module.min_blur_var
    assert metrics["sharpness_score"] >= 0.70
    assert metrics["glare_score"] < 0.05
    assert metrics["exposure_score"] >= 0.85
    assert metrics["overall_quality_score"] >= 0.75
    assert metrics["is_valid_quality"] is True
    assert metrics["resolution_w"] == 640
    assert metrics["resolution_h"] == 480


def test_assess_quality_blurry_photo(ingestion_module) -> None:
    """Test quality assessment on a heavily blurred photo."""
    img = _generate_synthetic_monument_image(width=640, height=480, blur=True, glare=False)
    metrics = ingestion_module.assess_quality(img)

    assert metrics["blur_score"] < ingestion_module.min_blur_var
    assert metrics["sharpness_score"] < 0.35
    assert metrics["is_valid_quality"] is False


def test_assess_quality_overexposed_photo(ingestion_module) -> None:
    """Test quality assessment on an overexposed/glare photo."""
    img = _generate_synthetic_monument_image(width=640, height=480, blur=False, glare=True)
    metrics = ingestion_module.assess_quality(img)

    assert metrics["glare_score"] > ingestion_module.max_glare_ratio
    assert metrics["exposure_score"] < 0.60
    assert metrics["is_valid_quality"] is False


def test_extract_exif_no_exif(ingestion_module) -> None:
    """Test extracting EXIF from an image with stripped/missing EXIF headers."""
    img = _generate_synthetic_monument_image()
    raw_bytes = _create_image_bytes_with_exif(img, include_exif=False)

    exif = ingestion_module.extract_exif(raw_bytes)
    assert isinstance(exif, dict)
    assert exif["camera_make"] is None
    assert exif["camera_model"] is None
    assert exif["gps_latitude"] is None
    assert exif["gps_longitude"] is None
    assert exif["gps_altitude"] is None
    assert exif["timestamp"] is None


def test_extract_exif_with_gps_telemetry(ingestion_module) -> None:
    """Test parsing camera metadata and converting DMS coordinates to decimal degrees."""
    img = _generate_synthetic_monument_image()
    raw_bytes = _create_image_bytes_with_exif(img, include_exif=True)

    exif = ingestion_module.extract_exif(raw_bytes)

    assert exif["camera_make"] == "Canon"
    assert exif["camera_model"] == "EOS 5D Mark IV"
    assert exif["orientation"] == 1
    assert exif["timestamp"] == datetime.datetime(2026, 5, 14, 10, 30, 0)

    # 12 deg + 58/60 + 45.50/3600 = 12.979306 deg N
    assert exif["gps_latitude"] is not None
    assert pytest.approx(exif["gps_latitude"], rel=1e-4) == 12.979306

    # 77 deg + 34/60 + 22.80/3600 = 77.573000 deg E
    assert exif["gps_longitude"] is not None
    assert pytest.approx(exif["gps_longitude"], rel=1e-4) == 77.573000

    assert exif["gps_altitude"] == 920.0


def test_register_image_and_segmentation(ingestion_module) -> None:
    """Test ORB feature matching and homography registration against reference image."""
    ref_img = _generate_synthetic_monument_image(width=600, height=450)

    M = cv2.getRotationMatrix2D((300, 225), 5.0, 0.95)
    query_img = cv2.warpAffine(ref_img, M, (600, 450))

    reg_result = ingestion_module.register_image(query_img, ref_img)

    assert reg_result["registration_success"] is True
    assert reg_result["homography_matrix"] is not None
    assert reg_result["inlier_count"] >= 4
    assert reg_result["confidence_score"] > 0.0

    reference_regions = [
        {
            "region_id": 101,
            "name": "left_column",
            "category": "pillar",
            "bounding_box": [90, 135, 60, 270],
        }
    ]
    projected = ingestion_module.segment_regions(
        query_img,
        homography_matrix=reg_result["homography_matrix"],
        reference_regions=reference_regions,
    )

    assert len(projected) == 1
    assert projected[0]["name"] == "left_column"
    assert len(projected[0]["bbox"]) == 4


def test_segment_regions_ai_path() -> None:
    """Test AI segmentation path calling mocked SAM and CLIP instances."""
    mock_sam = MagicMock(spec=SAMSegmenter)
    mock_clip = MagicMock(spec=CLIPRegionClassifier)

    dummy_mask = np.ones((400, 600), dtype=bool)
    mock_sam.generate_masks.return_value = [
        {"segmentation": dummy_mask, "bbox": [100, 80, 120, 240], "area": 28800}
    ]

    mock_clip.classify_masks.return_value = [
        {
            "bbox": [100, 80, 120, 240],
            "region_type": "stone pillar column",
            "confidence_score": 0.93,
            "all_scores": {"stone pillar column": 0.93, "arch": 0.04},
        }
    ]

    module = ImageIngestionModule(
        sam_segmenter=mock_sam,
        region_classifier=mock_clip,
        use_ai_segmentation=True,
    )

    img = np.zeros((400, 600, 3), dtype=np.uint8)
    regions = module.segment_regions(img, monument_id="TEST_MONUMENT")

    assert len(regions) == 1
    assert regions[0]["region_type"] == "stone pillar column"
    assert regions[0]["bbox"] == [100, 80, 120, 240]
    assert regions[0]["confidence_score"] == 0.93
    mock_sam.generate_masks.assert_called_once()
    mock_clip.classify_masks.assert_called_once()


def test_segment_regions_iou_db_matching(in_memory_db) -> None:
    """Test IoU-based matching: mapping overlapping bboxes to existing region rows."""
    mock_sam = MagicMock(spec=SAMSegmenter)
    mock_clip = MagicMock(spec=CLIPRegionClassifier)

    module = ImageIngestionModule(
        sam_segmenter=mock_sam,
        region_classifier=mock_clip,
        use_ai_segmentation=True,
        iou_threshold=0.5,
    )

    img = np.zeros((400, 600, 3), dtype=np.uint8)
    monument_uuid = module._resolve_monument_uuid("MONUMENT_01", db=in_memory_db)

    # 1. Photo 1: detects Arch at [100, 100, 150, 200]
    mock_sam.generate_masks.return_value = [{"bbox": [100, 100, 150, 200]}]
    mock_clip.classify_masks.return_value = [
        {"bbox": [100, 100, 150, 200], "region_type": "arched doorway entrance", "confidence_score": 0.9}
    ]

    res1 = module.segment_regions(img, monument_id="MONUMENT_01", db=in_memory_db)
    assert len(res1) == 1
    region_id_1 = res1[0]["region_id"]
    assert isinstance(region_id_1, (uuid.UUID, str))

    # Verify 1 Region created in DB
    assert in_memory_db.query(Region).filter_by(monument_id=monument_uuid).count() == 1

    # 2. Photo 2: detects the same Arch with slight shift [105, 98, 148, 204] (IoU > 0.85)
    mock_sam.generate_masks.return_value = [{"bbox": [105, 98, 148, 204]}]
    mock_clip.classify_masks.return_value = [
        {"bbox": [105, 98, 148, 204], "region_type": "arched doorway entrance", "confidence_score": 0.88}
    ]

    res2 = module.segment_regions(img, monument_id="MONUMENT_01", db=in_memory_db)
    assert len(res2) == 1
    # Must map to the SAME existing region_id and not create a duplicate row!
    assert res2[0]["region_id"] == region_id_1
    assert in_memory_db.query(Region).filter_by(monument_id=monument_uuid).count() == 1

    # 3. Photo 3: detects a completely new Dome at [350, 50, 180, 180] (IoU = 0.0)
    mock_sam.generate_masks.return_value = [{"bbox": [350, 50, 180, 180]}]
    mock_clip.classify_masks.return_value = [
        {"bbox": [350, 50, 180, 180], "region_type": "structural dome roof", "confidence_score": 0.95}
    ]

    res3 = module.segment_regions(img, monument_id="MONUMENT_01", db=in_memory_db)
    assert len(res3) == 1
    assert isinstance(res3[0]["region_id"], (uuid.UUID, str))
    assert res3[0]["region_id"] != region_id_1
    assert in_memory_db.query(Region).filter_by(monument_id=monument_uuid).count() == 2


def test_segment_regions_use_ai_segmentation_false_fallback() -> None:
    """Test that USE_AI_SEGMENTATION=False correctly uses homography projection."""
    module = ImageIngestionModule(use_ai_segmentation=False)
    img = np.zeros((400, 600, 3), dtype=np.uint8)
    H_identity = np.eye(3, dtype=np.float32)

    ref_regions = [
        {
            "region_id": 5,
            "name": "ref_dome",
            "category": "dome",
            "bounding_box": [50, 50, 200, 200],
        }
    ]

    res = module.segment_regions(
        image=img,
        homography_matrix=H_identity,
        reference_regions=ref_regions,
    )

    assert len(res) == 1
    assert res[0]["name"] == "ref_dome"
    assert res[0]["bbox"] == [50, 50, 200, 200]


def test_ingest_resilience_on_segment_error(in_memory_db) -> None:
    """Test that ingest() remains resilient and returns a valid response if segmentation fails."""
    module = ImageIngestionModule(use_ai_segmentation=False)

    # Force segment_regions to raise an error
    module.segment_regions = MagicMock(side_effect=RuntimeError("GPU OOM / Model Failure"))

    img_arr = _generate_synthetic_monument_image(width=640, height=480)
    img_bytes = _create_image_bytes_with_exif(img_arr, include_exif=True)

    response = module.ingest(
        image_bytes=img_bytes,
        monument_id="MONUMENT_ERROR_TEST",
        db=in_memory_db,
    )

    assert response.monument_id == "MONUMENT_ERROR_TEST"
    assert response.is_valid_quality is True
    assert response.matched_region_id is None
    assert response.observation_id is not None


def test_ingest_orchestration_with_db(ingestion_module, in_memory_db) -> None:
    """Test full end-to-end ingest() pipeline with database persistence."""
    img_arr = _generate_synthetic_monument_image(width=640, height=480)
    img_bytes = _create_image_bytes_with_exif(img_arr, include_exif=True)

    ref_img = _generate_synthetic_monument_image(width=640, height=480)

    response = ingestion_module.ingest(
        image_bytes=img_bytes,
        monument_id="MONUMENT_HAMPI_01",
        reference_image=ref_img,
        user_id="user_curator_42",
        db=in_memory_db,
    )

    assert response.monument_id == "MONUMENT_HAMPI_01"
    assert response.is_valid_quality is True
    assert response.resolution_w == 640
    assert response.resolution_h == 480
    assert response.exif is not None
    assert response.exif.camera_make == "Canon"
    assert response.registration_confidence is not None
    assert response.observation_id is not None

    # Verify DB persistence
    db_record = in_memory_db.query(Observation).filter_by(id=response.observation_id).first()
    assert db_record is not None
    assert db_record.user_id == "user_curator_42"
    assert db_record.blur_score == response.blur_score
    assert db_record.glare_score == response.glare_score
    assert db_record.sharpness_score == response.blur_score or db_record.sharpness_score is not None


def test_suggest_region_with_available_regions_and_no_auto_commit(in_memory_db) -> None:
    """Test suggest_region returns suggestions and available regions without writing new Region rows."""
    mock_sam = MagicMock(spec=SAMSegmenter)
    mock_clip = MagicMock(spec=CLIPRegionClassifier)

    module = ImageIngestionModule(
        sam_segmenter=mock_sam,
        region_classifier=mock_clip,
        use_ai_segmentation=True,
    )

    monument_uuid = module._resolve_monument_uuid("MONUMENT_SUGGEST_TEST", db=in_memory_db)

    # Pre-populate 2 regions in DB
    reg1 = Region(
        monument_id=monument_uuid,
        name="North Wall Facade",
        category="masonry wall facade",
        bounding_box=[100, 100, 200, 200],
    )
    reg2 = Region(
        monument_id=monument_uuid,
        name="South Pillar Array",
        category="stone pillar column",
        bounding_box=[350, 100, 150, 300],
    )
    in_memory_db.add_all([reg1, reg2])
    in_memory_db.commit()

    initial_region_count = in_memory_db.query(Region).filter_by(monument_id=monument_uuid).count()
    assert initial_region_count == 2

    # Mock AI to detect "masonry wall facade" at [105, 95, 195, 205] (matches reg1)
    mock_sam.generate_masks.return_value = [{"bbox": [105, 95, 195, 205]}]
    mock_clip.classify_masks.return_value = [
        {"bbox": [105, 95, 195, 205], "region_type": "masonry wall facade", "confidence_score": 0.94}
    ]

    img_arr = _generate_synthetic_monument_image(width=640, height=480)
    img_bytes = _create_image_bytes_with_exif(img_arr, include_exif=False)

    suggestion = module.suggest_region(
        image_bytes=img_bytes,
        monument_id=str(monument_uuid),
        db=in_memory_db,
    )

    assert suggestion["monument_id"] == str(monument_uuid)
    assert suggestion["suggested_region_id"] == str(reg1.id)
    assert suggestion["suggested_region_name"] == "North Wall Facade"
    assert suggestion["confidence_score"] >= 0.8
    assert len(suggestion["available_regions"]) == 2

    # Crucial: verify that suggest_region DID NOT commit any new rows to DB
    final_region_count = in_memory_db.query(Region).filter_by(monument_id=monument_uuid).count()
    assert final_region_count == initial_region_count


def test_cold_start_baseline_and_sequential_alignment(ingestion_module, in_memory_db) -> None:
    """Test that first upload is marked baseline, and second upload aligns against the first."""
    monument_uuid = ingestion_module._resolve_monument_uuid("MONUMENT_SEQ_TEST", db=in_memory_db)

    test_region = Region(
        monument_id=monument_uuid,
        name="Sanctuary Tower",
        category="structural dome roof",
        bounding_box=[100, 100, 300, 300],
    )
    in_memory_db.add(test_region)
    in_memory_db.commit()
    in_memory_db.refresh(test_region)

    # 1. Cold Start Observation (First upload for this region)
    img1_arr = _generate_synthetic_monument_image(width=640, height=480)
    img1_bytes = _create_image_bytes_with_exif(img1_arr, include_exif=True)

    res1 = ingestion_module.ingest(
        image_bytes=img1_bytes,
        monument_id=str(monument_uuid),
        region_id=str(test_region.id),
        user_id="expert_user_1",
        db=in_memory_db,
    )

    assert res1.matched_region_id == test_region.id
    assert res1.is_baseline is True
    assert res1.registration_success is True
    assert res1.registration_confidence == 1.0

    # 2. Verify get_latest_observation helper
    latest_obs = ingestion_module.get_latest_observation(in_memory_db, test_region.id)
    assert latest_obs is not None
    assert latest_obs.id == res1.observation_id

    # 3. Second Observation (Sequential upload for the same region)
    img2_arr = _generate_synthetic_monument_image(width=640, height=480)
    img2_bytes = _create_image_bytes_with_exif(img2_arr, include_exif=True)

    res2 = ingestion_module.ingest(
        image_bytes=img2_bytes,
        monument_id=str(monument_uuid),
        region_id=str(test_region.id),
        user_id="expert_user_2",
        db=in_memory_db,
    )

    assert res2.matched_region_id == test_region.id
    assert res2.is_baseline is False
    assert res2.registration_success is True
    assert res2.observation_id != res1.observation_id

    # 4. Storage sequence check: verify both observations exist ordered by timestamp
    all_obs = (
        in_memory_db.query(Observation)
        .filter(Observation.region_id == test_region.id)
        .order_by(Observation.created_at.asc())
        .all()
    )
    assert len(all_obs) == 2
    assert all_obs[0].id == res1.observation_id
    assert all_obs[1].id == res2.observation_id

