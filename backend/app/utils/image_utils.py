"""Shared computer vision helpers using OpenCV and PIL."""

from typing import Tuple, Optional, Union
import io
from pathlib import Path
import cv2
import numpy as np
from PIL import Image


def load_image_cv2(image_input: Union[str, Path, bytes]) -> np.ndarray:
    """Load image from a file path, HTTP URL, or raw bytes as a BGR OpenCV ndarray."""
    import urllib.request

    if isinstance(image_input, (str, Path)):
        path_str = str(image_input)
        if path_str.startswith("http://") or path_str.startswith("https://"):
            try:
                req = urllib.request.Request(path_str, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                nparr = np.frombuffer(data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    return img
            except Exception as e:
                raise ValueError(f"Unable to fetch image from URL '{path_str}': {e}")

        img = cv2.imread(path_str, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Unable to load image from path: {path_str}")
        return img
    elif isinstance(image_input, (bytes, bytearray)):
        nparr = np.frombuffer(image_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Unable to decode image from provided byte buffer.")
        return img
    else:
        raise TypeError(f"Unsupported image input type: {type(image_input)}")


def load_image_pil(image_input: Union[str, Path, bytes]) -> Image.Image:
    """Load image from a file path, HTTP URL, or raw bytes as a PIL Image."""
    import urllib.request

    try:
        if isinstance(image_input, (str, Path)):
            path_str = str(image_input)
            if path_str.startswith("http://") or path_str.startswith("https://"):
                req = urllib.request.Request(path_str, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                return Image.open(io.BytesIO(data))
            img = Image.open(path_str)
            img.load()
            return img
        elif isinstance(image_input, (bytes, bytearray)):
            img = Image.open(io.BytesIO(image_input))
            img.load()
            return img
        elif isinstance(image_input, Image.Image):
            return image_input
        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")
    except Exception as exc:
        raise ValueError(f"Failed to load PIL image: {str(exc)}") from exc


def compute_laplacian_variance(image: np.ndarray) -> float:
    """Compute focus blur metric using variance of the Laplacian operator.

    Algorithm:
        1. Convert image to single-channel grayscale if multidimensional.
        2. Convolve with 3x3 Laplacian kernel in 64-bit float precision.
        3. Compute statistical variance of the second derivatives.
        Lower variance indicates blur; higher variance indicates sharp edges.

    Args:
        image: Grayscale or BGR/RGB image array.

    Returns:
        float: Laplacian variance metric (higher = sharper).
    """
    if image is None or image.size == 0:
        return 0.0

    if len(image.shape) == 3 and image.shape[2] >= 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif len(image.shape) == 2:
        gray = image
    else:
        gray = image[:, :, 0]

    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = float(laplacian.var())
    return variance


def detect_glare_ratio(image: np.ndarray, threshold: int = 240) -> float:
    """Calculate the ratio of overexposed/glare saturated pixels.

    Args:
        image: BGR, RGB, or Grayscale image array.
        threshold: Pixel intensity threshold (0-255) above which pixel is considered glare.

    Returns:
        float: Saturated pixel ratio in range [0.0, 1.0].
    """
    if image is None or image.size == 0:
        return 0.0

    if len(image.shape) == 3 and image.shape[2] >= 3:
        # All color channels saturated
        glare_mask = np.all(image[:, :, :3] >= threshold, axis=-1)
    else:
        glare_mask = image >= threshold

    total_pixels = glare_mask.size
    if total_pixels == 0:
        return 0.0

    glare_count = np.count_nonzero(glare_mask)
    return float(glare_count / total_pixels)


def align_homography(
    src_image: np.ndarray, dst_shape: Tuple[int, int], H_matrix: np.ndarray
) -> np.ndarray:
    """Warp source image using a 3x3 homography transformation matrix.

    Args:
        src_image: Source image array to warp.
        dst_shape: Target canvas dimensions as (height, width).
        H_matrix: 3x3 perspective homography matrix.

    Returns:
        np.ndarray: Warped image registered to target dimensions.
    """
    if H_matrix is None:
        raise ValueError("Homography matrix H_matrix cannot be None for alignment.")

    height, width = dst_shape[:2]
    warped = cv2.warpPerspective(
        src_image,
        H_matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0),
    )
    return warped
