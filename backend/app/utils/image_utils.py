"""Shared computer vision helpers using OpenCV and PIL."""

from typing import Tuple, Optional
import cv2
import numpy as np
from PIL import Image


def load_image_cv2(image_path: str) -> np.ndarray:
    """Load image from path as BGR OpenCV ndarray."""
    pass


def load_image_pil(image_path: str) -> Image.Image:
    """Load image from path as PIL Image."""
    pass


def compute_laplacian_variance(image_gray: np.ndarray) -> float:
    """Compute focus blur metric using variance of the Laplacian."""
    pass


def detect_glare_ratio(image_bgr: np.ndarray, threshold: int = 245) -> float:
    """Calculate ratio of overexposed/glare saturated pixels."""
    pass


def align_homography(
    src_image: np.ndarray, dst_shape: Tuple[int, int], H_matrix: np.ndarray
) -> np.ndarray:
    """Warp source image using 3x3 homography transformation matrix."""
    pass
