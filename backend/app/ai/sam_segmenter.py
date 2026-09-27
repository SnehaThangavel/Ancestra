"""Segment Anything Model (SAM) wrapper for zero-shot architectural region segmentation.

SESCI Architecture - AI Upgrade:
Provides automated, high-precision architectural mask segmentation for monument photos
using Meta AI's Segment Anything Model (SAM), with dynamic letterboxed padding and
noise mask filtering.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import cv2
import numpy as np
import torch
try:
    from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
except ImportError:
    sam_model_registry = None
    SamAutomaticMaskGenerator = None

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Official download URLs for SAM model checkpoints
SAM_DOWNLOAD_URLS = {
    "vit_b": "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth",
    "vit_l": "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth",
    "vit_h": "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth",
}


class SAMSegmenter:
    """Wraps SAM model to extract fine-grained architectural segment masks from photos."""

    def __init__(
        self,
        checkpoint_path: Optional[str] = None,
        model_type: Optional[str] = None,
        device: Optional[str] = None,
        auto_load: bool = False,
        min_mask_area_ratio: Optional[float] = None,
        points_per_side: Optional[int] = None,
        pred_iou_thresh: Optional[float] = None,
        stability_score_thresh: Optional[float] = None,
        min_mask_region_area: Optional[int] = None,
    ) -> None:
        """Initialize SAM segmenter settings and device configuration.

        Args:
            checkpoint_path: Path to the .pth SAM checkpoint file.
            model_type: SAM architecture type ('vit_b', 'vit_l', 'vit_h').
            device: Torch execution device ('cuda', 'cpu', or None for auto-detect).
            auto_load: If True, immediately load model weights on instantiation.
            min_mask_area_ratio: Minimum relative area (mask_pixels / total_pixels) to keep.
            points_per_side: Number of point prompts per side for automatic mask generation.
            pred_iou_thresh: Predicted IoU filtering threshold for mask quality.
            stability_score_thresh: Stability score filtering threshold for mask stability.
            min_mask_region_area: Minimum pixel area for disconnected mask components.
        """
        self.checkpoint_path = checkpoint_path or settings.SAM_CHECKPOINT_PATH
        self.model_type = model_type or settings.SAM_MODEL_TYPE

        # Device selection (CUDA GPU if available, else CPU)
        if device is not None:
            self.device = device
        else:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(
            f"Initializing SAMSegmenter (model_type='{self.model_type}', "
            f"device='{self.device}', checkpoint='{self.checkpoint_path}')"
        )

        self.min_mask_area_ratio = (
            min_mask_area_ratio
            if min_mask_area_ratio is not None
            else getattr(settings, "MIN_MASK_AREA_RATIO", 0.005)
        )
        self.points_per_side = (
            points_per_side
            if points_per_side is not None
            else getattr(settings, "SAM_POINTS_PER_SIDE", 32)
        )
        self.pred_iou_thresh = (
            pred_iou_thresh
            if pred_iou_thresh is not None
            else getattr(settings, "SAM_PRED_IOU_THRESH", 0.86)
        )
        self.stability_score_thresh = (
            stability_score_thresh
            if stability_score_thresh is not None
            else getattr(settings, "SAM_STABILITY_SCORE_THRESH", 0.92)
        )
        self.min_mask_region_area = (
            min_mask_region_area
            if min_mask_region_area is not None
            else getattr(settings, "SAM_MIN_MASK_REGION_AREA", 500)
        )

        self.model: Optional[torch.nn.Module] = None
        self.mask_generator: Optional[SamAutomaticMaskGenerator] = None

        if auto_load:
            self.load_model()

    def load_model(self) -> None:
        """Load SAM checkpoint weights into memory/GPU and initialize mask generator.

        Raises:
            FileNotFoundError: If the configured checkpoint file is not found on disk.
            ValueError: If the specified model_type is unsupported.
        """
        if self.model is not None and self.mask_generator is not None:
            return  # Already loaded

        checkpoint_file = Path(self.checkpoint_path)
        if not checkpoint_file.is_file():
            download_url = SAM_DOWNLOAD_URLS.get(
                self.model_type,
                "https://github.com/facebookresearch/segment-anything#model-checkpoints",
            )
            error_msg = (
                f"SAM checkpoint file not found at '{self.checkpoint_path}'. "
                f"Please download the '{self.model_type}' weights from: {download_url} "
                f"and save them to '{self.checkpoint_path}'."
            )
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        if self.model_type not in sam_model_registry:
            valid_types = list(sam_model_registry.keys())
            raise ValueError(
                f"Unsupported SAM model_type '{self.model_type}'. Supported types: {valid_types}"
            )

        logger.info(f"Loading SAM weights ({self.model_type}) from '{self.checkpoint_path}'...")
        sam = sam_model_registry[self.model_type](checkpoint=str(checkpoint_file))
        sam.to(device=self.device)
        self.model = sam

        logger.info(
            f"Initializing SamAutomaticMaskGenerator (points_per_side={self.points_per_side}, "
            f"pred_iou_thresh={self.pred_iou_thresh}, stability_score_thresh={self.stability_score_thresh})"
        )
        self.mask_generator = SamAutomaticMaskGenerator(
            model=self.model,
            points_per_side=self.points_per_side,
            pred_iou_thresh=self.pred_iou_thresh,
            stability_score_thresh=self.stability_score_thresh,
            min_mask_region_area=self.min_mask_region_area,
        )
        logger.info("SAM model and mask generator successfully loaded.")

    @staticmethod
    def get_relative_area(
        mask: Union[Dict[str, Any], np.ndarray], img_w: int, img_h: int
    ) -> float:
        """Calculate the proportion of the image area occupied by the mask.

        Args:
            mask: Binary mask 2D boolean/uint8 array or SAM mask dictionary with 'segmentation'.
            img_w: Total image width in pixels.
            img_h: Total image height in pixels.

        Returns:
            float: Relative mask area ratio in [0.0, 1.0].
        """
        if img_w <= 0 or img_h <= 0:
            return 0.0

        if isinstance(mask, dict):
            seg = mask.get("segmentation")
            if seg is None:
                area = mask.get("area", 0)
                return float(area) / float(img_w * img_h)
            mask_arr = seg
        else:
            mask_arr = mask

        mask_pixels = int(np.count_nonzero(mask_arr))
        total_pixels = float(img_w * img_h)
        return float(mask_pixels / total_pixels)

    def generate_masks(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Generate architectural component segment masks for an input photo.

        Args:
            image: Input image as BGR or RGB OpenCV ndarray.

        Returns:
            List[Dict[str, Any]]: Filtered list of SAM mask dictionaries, each containing:
                - 'segmentation': 2D boolean mask ndarray
                - 'area': int mask pixel area
                - 'bbox': [x, y, w, h] bounding box
                - 'predicted_iou': float
                - 'stability_score': float
        """
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            return []

        if self.mask_generator is None:
            self.load_model()

        img_h, img_w = image.shape[:2]

        # SAM expects RGB format
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        elif len(image.shape) == 2:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            rgb_image = image[:, :, :3]

        # Generate raw masks via SAM
        raw_masks = self.mask_generator.generate(rgb_image)

        # Filter out tiny noise masks below MIN_MASK_AREA_RATIO
        filtered_masks: List[Dict[str, Any]] = []
        for m in raw_masks:
            rel_area = self.get_relative_area(m, img_w, img_h)
            if rel_area >= self.min_mask_area_ratio:
                filtered_masks.append(m)

        logger.debug(
            f"Generated {len(raw_masks)} raw SAM masks, retained {len(filtered_masks)} "
            f"after filtering (min_area_ratio={self.min_mask_area_ratio})"
        )
        return filtered_masks

    def clip_and_clean_mask(
        self,
        image: np.ndarray,
        mask_dict: Union[Dict[str, Any], np.ndarray],
        img_w: Optional[int] = None,
        img_h: Optional[int] = None,
        pad_ratio: float = 0.1,
        target_size: int = 224,
    ) -> np.ndarray:
        """Isolate masked object, apply dynamic scaled padding, and letterbox into square RGB crop.

        Processing Pipeline:
            a) Extracts tight bounding box from the boolean mask via np.where.
            b) Applies dynamic padding proportional to object dimensions (pad_ratio * w/h),
               clamped to image boundaries.
            c) Zeroes out background pixels outside the mask (image[~mask] = 0).
            d) Crops to the padded bounding box.
            e) Resizes to square target_size (default 224) preserving aspect ratio via
               letterbox border padding (cv2.copyMakeBorder), avoiding spatial distortion.
            f) Converts BGR color format to standard RGB format.

        Args:
            image: Source image array (BGR or RGB).
            mask_dict: SAM mask dictionary with 'segmentation' or direct 2D boolean array.
            img_w: Optional width override (defaults to image.shape[1]).
            img_h: Optional height override (defaults to image.shape[0]).
            pad_ratio: Relative padding factor scaled to object width/height.
            target_size: Output square dimensions (width=height=target_size).

        Returns:
            np.ndarray: Cleaned, letterboxed RGB crop of shape (target_size, target_size, 3).
        """
        if image is None or image.size == 0:
            return np.zeros((target_size, target_size, 3), dtype=np.uint8)

        actual_h, actual_w = image.shape[:2]
        img_w = img_w or actual_w
        img_h = img_h or actual_h

        # Extract boolean mask
        if isinstance(mask_dict, dict):
            mask = mask_dict.get("segmentation")
            if mask is None:
                mask = np.ones((actual_h, actual_w), dtype=bool)
        else:
            mask = mask_dict

        mask = np.asarray(mask, dtype=bool)

        # a) Compute tight bbox via np.where
        y_indices, x_indices = np.where(mask)
        if len(y_indices) == 0 or len(x_indices) == 0:
            return np.zeros((target_size, target_size, 3), dtype=np.uint8)

        min_y, max_y = int(np.min(y_indices)), int(np.max(y_indices))
        min_x, max_x = int(np.min(x_indices)), int(np.max(x_indices))

        obj_w = max_x - min_x + 1
        obj_h = max_y - min_y + 1

        # b) Add dynamic padding scaled to the object's dimensions
        pad_x = int(obj_w * pad_ratio)
        pad_y = int(obj_h * pad_ratio)

        x1 = max(0, min_x - pad_x)
        y1 = max(0, min_y - pad_y)
        x2 = min(actual_w, max_x + 1 + pad_x)
        y2 = min(actual_h, max_y + 1 + pad_y)

        # c) Zero out background pixels outside the mask
        masked_img = image.copy()
        if len(masked_img.shape) == 3:
            masked_img[~mask] = 0
        else:
            masked_img[~mask] = 0

        # d) Crop to the padded bbox
        crop = masked_img[y1:y2, x1:x2]
        if crop.size == 0:
            return np.zeros((target_size, target_size, 3), dtype=np.uint8)

        # e) Resize to square target size preserving aspect ratio via letterboxing
        crop_h, crop_w = crop.shape[:2]
        scale = target_size / max(crop_h, crop_w)
        new_w = max(1, int(round(crop_w * scale)))
        new_h = max(1, int(round(crop_h * scale)))

        resized = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Letterbox padding calculation
        pad_top = (target_size - new_h) // 2
        pad_bottom = target_size - new_h - pad_top
        pad_left = (target_size - new_w) // 2
        pad_right = target_size - new_w - pad_left

        if len(resized.shape) == 3:
            border_val = (0, 0, 0)
        else:
            border_val = 0

        square_crop = cv2.copyMakeBorder(
            resized,
            pad_top,
            pad_bottom,
            pad_left,
            pad_right,
            cv2.BORDER_CONSTANT,
            value=border_val,
        )

        # f) Convert BGR to RGB
        if len(square_crop.shape) == 3 and square_crop.shape[2] >= 3:
            rgb_crop = cv2.cvtColor(square_crop[:, :, :3], cv2.COLOR_BGR2RGB)
        elif len(square_crop.shape) == 2:
            rgb_crop = cv2.cvtColor(square_crop, cv2.COLOR_GRAY2RGB)
        else:
            rgb_crop = square_crop

        return rgb_crop
