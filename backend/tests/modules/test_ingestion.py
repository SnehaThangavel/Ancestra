"""Tests for Module 1 (Image Ingestion & Registration)."""

import io
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


@pytest.fixture
def ingestion_module() -> ImageIngestionModule:
    """Fixture providing initialized ImageIngestionModule."""
    return ImageIngestionModule(
        min_width=400,
        min_height=300,
        min_blur_var=80.0,
        max_glare_ratio=0.25,
        min_quality_threshold=0.35,
    )


@pytest.fixture
def in_memory_db():
    """Fixture providing an isolated SQLite database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()


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
        # Simulate severe sun overexposure / glare spot (>240 in all channels)
        img[int(height * 0.1) : int(height * 0.6), int(width * 0.2) : int(width * 0.8)] = 252

    if blur:
        # Simulate severe out-of-focus blur
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
    # Make: Canon, Model: EOS 5D
    exif[271] = "Canon"
    exif[272] = "EOS 5D Mark IV"
    exif[274] = 1  # Normal orientation
    exif[306] = "2026:05:14 10:30:00"  # DateTime

    # GPS IFD tags
    gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
    gps_ifd[1] = "N"           # GPSLatitudeRef
    gps_ifd[2] = (12.0, 58.0, 45.50)  # 12 deg, 58 min, 45.50 sec
    gps_ifd[3] = "E"           # GPSLongitudeRef
    gps_ifd[4] = (77.0, 34.0, 22.80)  # 77 deg, 34 min, 22.80 sec
    gps_ifd[5] = 0             # GPSAltitudeRef (above sea level)
    gps_ifd[6] = 920.0         # GPSAltitude = 920m
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

    # Altitude 920m
    assert exif["gps_altitude"] == 920.0


def test_register_image_and_segmentation(ingestion_module) -> None:
    """Test ORB feature matching and homography registration against reference image."""
    ref_img = _generate_synthetic_monument_image(width=600, height=450)

    # Apply a slight affine warp (scale + rotation + translation) to create query image
    M = cv2.getRotationMatrix2D((300, 225), 5.0, 0.95)
    query_img = cv2.warpAffine(ref_img, M, (600, 450))

    reg_result = ingestion_module.register_image(query_img, ref_img)

    assert reg_result["registration_success"] is True
    assert reg_result["homography_matrix"] is not None
    assert reg_result["inlier_count"] >= 4
    assert reg_result["confidence_score"] > 0.0

    # Test region projection with homography
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
    assert projected[0]["region_id"] == 101
    assert projected[0]["name"] == "left_column"
    assert len(projected[0]["bbox"]) == 4
    assert len(projected[0]["polygon"]) == 4


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
    assert response.observation_id > 0

    # Verify DB persistence
    db_record = in_memory_db.query(Observation).filter_by(id=response.observation_id).first()
    assert db_record is not None
    assert db_record.monument_id == "MONUMENT_HAMPI_01"
    assert db_record.user_id == "user_curator_42"
    assert db_record.blur_score == response.blur_score
    assert db_record.glare_score == response.glare_score
