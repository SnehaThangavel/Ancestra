"""Tests for shared image utilities."""

import io
import pytest
import numpy as np
import cv2
from PIL import Image

from app.utils.image_utils import (
    compute_laplacian_variance,
    detect_glare_ratio,
    load_image_cv2,
    load_image_pil,
    align_homography,
)


def test_image_utils_blur_glare() -> None:
    """Test image blur and glare metric calculations."""
    # 1. Create a sharp image with high frequency edges (checkerboard pattern)
    sharp_img = np.zeros((400, 500, 3), dtype=np.uint8)
    for i in range(0, 400, 20):
        for j in range(0, 500, 20):
            if (i // 20 + j // 20) % 2 == 0:
                sharp_img[i : i + 20, j : j + 20] = [200, 200, 200]
            else:
                sharp_img[i : i + 20, j : j + 20] = [30, 30, 30]

    # 2. Create a heavily blurred version
    blurry_img = cv2.GaussianBlur(sharp_img, (51, 51), 0)

    sharp_var = compute_laplacian_variance(sharp_img)
    blurry_var = compute_laplacian_variance(blurry_img)

    assert sharp_var > 100.0, f"Expected sharp variance > 100, got {sharp_var}"
    assert blurry_var < sharp_var, "Blurry variance must be significantly less than sharp variance"
    assert blurry_var < 50.0, f"Expected blurry variance < 50, got {blurry_var}"

    # 3. Test glare detection
    normal_img = np.full((300, 400, 3), 128, dtype=np.uint8)
    glare_img = np.full((300, 400, 3), 250, dtype=np.uint8)
    half_glare = normal_img.copy()
    half_glare[:150, :] = 255

    assert detect_glare_ratio(normal_img) == 0.0
    assert detect_glare_ratio(glare_img) == 1.0
    assert pytest.approx(detect_glare_ratio(half_glare), 0.01) == 0.5


def test_image_loading_helpers(tmp_path) -> None:
    """Test load_image_cv2 and load_image_pil for file paths and raw byte buffers."""
    sample_arr = np.full((100, 100, 3), 100, dtype=np.uint8)
    cv2.circle(sample_arr, (50, 50), 20, (200, 50, 50), -1)

    # Encode to PNG bytes
    success, buffer = cv2.imencode(".png", sample_arr)
    assert success
    img_bytes = buffer.tobytes()

    # Load from bytes
    loaded_cv2 = load_image_cv2(img_bytes)
    assert loaded_cv2.shape == (100, 100, 3)

    loaded_pil = load_image_pil(img_bytes)
    assert loaded_pil.size == (100, 100)

    # Save to disk and load from path
    img_file = tmp_path / "test.png"
    img_file.write_bytes(img_bytes)

    loaded_from_disk = load_image_cv2(img_file)
    assert loaded_from_disk.shape == (100, 100, 3)

    pil_from_disk = load_image_pil(img_file)
    assert pil_from_disk.size == (100, 100)


def test_align_homography() -> None:
    """Test warping an image using an identity homography matrix."""
    src_img = np.full((200, 300, 3), 150, dtype=np.uint8)
    H_identity = np.eye(3, dtype=np.float32)

    warped = align_homography(src_img, (200, 300), H_identity)
    assert warped.shape == (200, 300, 3)
    assert np.allclose(warped, src_img)
