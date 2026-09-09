"""Tests for SAM segmenter wrapper."""

from unittest.mock import MagicMock
import pytest
import numpy as np
import cv2

from app.ai.sam_segmenter import SAMSegmenter


@pytest.fixture
def sam_segmenter() -> SAMSegmenter:
    """Fixture providing initialized SAMSegmenter with custom settings."""
    return SAMSegmenter(
        checkpoint_path="nonexistent_checkpoint_test.pth",
        model_type="vit_b",
        device="cpu",
        min_mask_area_ratio=0.01,
    )


def test_sam_segmenter_init(sam_segmenter: SAMSegmenter) -> None:
    """Test SAMSegmenter initialization and configuration parameters."""
    assert sam_segmenter.model_type == "vit_b"
    assert sam_segmenter.device == "cpu"
    assert sam_segmenter.min_mask_area_ratio == 0.01
    assert sam_segmenter.model is None
    assert sam_segmenter.mask_generator is None


def test_sam_segmenter_missing_checkpoint_error() -> None:
    """Test clear FileNotFoundError when checkpoint file does not exist."""
    segmenter = SAMSegmenter(
        checkpoint_path="missing_weights/sam_vit_b.pth",
        model_type="vit_b",
        auto_load=False,
    )
    with pytest.raises(FileNotFoundError) as exc_info:
        segmenter.load_model()

    assert "SAM checkpoint file not found" in str(exc_info.value)
    assert "https://dl.fbaipublicfiles.com/segment_anything" in str(exc_info.value)


def test_get_relative_area(sam_segmenter: SAMSegmenter) -> None:
    """Test mask relative area calculation for binary arrays and SAM dicts."""
    img_w, img_h = 200, 100
    total_pixels = 200 * 100  # 20,000

    # 1. 2D Boolean mask covering 2,000 pixels (10% of image)
    mask_arr = np.zeros((100, 200), dtype=bool)
    mask_arr[:20, :100] = True  # 20 * 100 = 2,000 pixels
    rel_area = sam_segmenter.get_relative_area(mask_arr, img_w, img_h)
    assert pytest.approx(rel_area, 1e-4) == 0.10

    # 2. SAM mask dictionary
    sam_dict = {"segmentation": mask_arr, "area": 2000}
    rel_area_dict = sam_segmenter.get_relative_area(sam_dict, img_w, img_h)
    assert pytest.approx(rel_area_dict, 1e-4) == 0.10


def test_clip_and_clean_mask(sam_segmenter: SAMSegmenter) -> None:
    """Test dynamic padding, background zeroing, and letterbox square cropping."""
    # Create 300x400 BGR canvas with a blue rectangular object
    image = np.full((300, 400, 3), 100, dtype=np.uint8)
    # Object: column from (y: 50..200, x: 100..150) -> h=151, w=51
    image[50:201, 100:151] = [220, 50, 50]  # Blue-ish BGR

    # Create mask for this column
    mask = np.zeros((300, 400), dtype=bool)
    mask[50:201, 100:151] = True

    crop = sam_segmenter.clip_and_clean_mask(
        image=image,
        mask_dict=mask,
        pad_ratio=0.1,
        target_size=224,
    )

    # 1. Output must be exactly target_size x target_size x 3
    assert crop.shape == (224, 224, 3)
    assert crop.dtype == np.uint8

    # 2. Letterbox borders (corners) should be zeroed (black)
    assert np.all(crop[0, 0] == [0, 0, 0])
    assert np.all(crop[223, 223] == [0, 0, 0])

    # 3. Center of object should contain the converted RGB color (Red channel from Blue BGR)
    center_pixel = crop[112, 112]
    # In BGR [220, 50, 50] -> converted to RGB [50, 50, 220]
    assert center_pixel[2] == 220 or center_pixel[0] == 50


def test_generate_masks_with_noise_filtering(sam_segmenter: SAMSegmenter) -> None:
    """Test that generate_masks filters out noise masks below MIN_MASK_AREA_RATIO."""
    img_h, img_w = 400, 600
    dummy_img = np.zeros((img_h, img_w, 3), dtype=np.uint8)

    # Mock mask generator returning 1 large mask (pillar) and 1 tiny noise mask (speck)
    large_mask = np.zeros((img_h, img_w), dtype=bool)
    large_mask[50:250, 100:200] = True  # Area = 20,000 pixels -> ratio = 20,000 / 240,000 = 0.0833 (> 0.01)

    tiny_mask = np.zeros((img_h, img_w), dtype=bool)
    tiny_mask[10:15, 10:15] = True  # Area = 25 pixels -> ratio = 25 / 240,000 = 0.0001 (< 0.01)

    mock_generator = MagicMock()
    mock_generator.generate.return_value = [
        {"segmentation": large_mask, "area": 20000, "bbox": [100, 50, 100, 200]},
        {"segmentation": tiny_mask, "area": 25, "bbox": [10, 10, 5, 5]},
    ]
    sam_segmenter.mask_generator = mock_generator

    results = sam_segmenter.generate_masks(dummy_img)

    assert len(results) == 1
    assert results[0]["area"] == 20000
