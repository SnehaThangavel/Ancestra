"""OpenCLIP zero-shot classifier for SAM architectural mask components.

SESCI Architecture - AI Upgrade:
Performs zero-shot semantic categorization of segmented architectural regions
(pillars, domes, arches, facades, carvings, inscriptions) and filters out
transient/negative non-structural elements (tourists, sky, vegetation, vehicles).
"""

from typing import List, Dict, Any, Optional, Union, Set
import numpy as np
import torch
from PIL import Image
try:
    import open_clip
except ImportError:
    open_clip = None

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CLIPRegionClassifier:
    """Zero-shot semantic classification of masked monument components using OpenCLIP."""

    DEFAULT_CLASSES = [
        "stone pillar column",
        "structural dome roof",
        "arched doorway entrance",
        "masonry wall facade",
        "carved stone sculpture",
        "ancient stone inscription",
        "decorative carved frieze",
        "weathered foundation base",
        "person or tourist",
        "vegetation or trees",
        "clear or cloudy sky",
        "vehicle or modern object",
    ]

    DEFAULT_NEGATIVE_CLASSES = [
        "person or tourist",
        "vegetation or trees",
        "clear or cloudy sky",
        "vehicle or modern object",
    ]

    def __init__(
        self,
        model_name: Optional[str] = None,
        pretrained: Optional[str] = None,
        device: Optional[str] = None,
        auto_load: bool = False,
        region_labels: Optional[List[str]] = None,
        negative_labels: Optional[List[str]] = None,
    ) -> None:
        """Initialize OpenCLIP zero-shot classifier configuration.

        Args:
            model_name: OpenCLIP model architecture name (e.g. 'ViT-B-32').
            pretrained: Dataset tag for pretrained weights (e.g. 'laion2b_s34b_b79k').
            device: Torch execution device ('cuda', 'cpu', or None for auto-detect).
            auto_load: If True, immediately load model and tokenizer into memory.
            region_labels: List of candidate class prompt strings.
            negative_labels: Subset of labels considered non-structural/negative.
        """
        self.model_name = model_name or getattr(settings, "CLIP_MODEL_NAME", "ViT-B-32")
        self.pretrained = pretrained or getattr(settings, "CLIP_PRETRAINED", "laion2b_s34b_b79k")

        # Device selection (CUDA GPU if available, else CPU)
        if device is not None:
            self.device = device
        else:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(
            f"Initializing CLIPRegionClassifier (model='{self.model_name}', "
            f"pretrained='{self.pretrained}', device='{self.device}')`"
        )

        # Configurable class labels
        config_labels = getattr(settings, "CLIP_REGION_LABELS", None)
        self.region_labels = region_labels or config_labels or self.DEFAULT_CLASSES

        config_negatives = getattr(settings, "CLIP_NEGATIVE_LABELS", None)
        self.negative_labels: Set[str] = set(
            negative_labels or config_negatives or self.DEFAULT_NEGATIVE_CLASSES
        )

        self.model: Optional[torch.nn.Module] = None
        self.preprocess: Optional[Any] = None
        self.tokenizer: Optional[Any] = None

        if auto_load:
            self.load_model()

    def load_model(self) -> None:
        """Load OpenCLIP model, preprocessing transforms, and tokenizer into memory/GPU.

        Raises:
            Exception: If OpenCLIP model weights fail to load.
        """
        if self.model is not None and self.preprocess is not None and self.tokenizer is not None:
            return  # Already loaded

        logger.info(f"Loading OpenCLIP '{self.model_name}' (pretrained='{self.pretrained}')...")
        try:
            model, _, preprocess = open_clip.create_model_and_transforms(
                self.model_name,
                pretrained=self.pretrained,
                device=self.device,
            )
            model.eval()

            tokenizer = open_clip.get_tokenizer(self.model_name)

            self.model = model
            self.preprocess = preprocess
            self.tokenizer = tokenizer
            logger.info("OpenCLIP model and tokenizer successfully loaded.")
        except Exception as err:
            logger.error(f"Failed to load OpenCLIP model: {err}")
            raise

    def is_negative_label(self, label: str) -> bool:
        """Check whether a predicted class label corresponds to a non-structural element.

        Args:
            label: Text label to check.

        Returns:
            bool: True if the label represents transient or negative content.
        """
        if not label:
            return False

        normalized = label.strip().lower()
        if normalized in self.negative_labels:
            return True

        # Substring heuristics for common non-structural categories
        for neg in ("person", "tourist", "tree", "vegetation", "sky", "cloud", "vehicle", "car"):
            if neg in normalized:
                return True

        return False

    def classify_crop(
        self,
        crop: Union[np.ndarray, Image.Image],
        candidate_labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Classify a single architectural crop image using CLIP image-text similarity.

        Algorithm:
            1. Preprocesses crop into normalized PyTorch tensor.
            2. Tokenizes text candidate prompt strings.
            3. Encodes normalized visual and textual embeddings.
            4. Calculates scaled cosine similarity: S = 100 * (E_img @ E_text.T).
            5. Computes softmax probability distribution over the label set.
            6. Returns top predicted label, confidence score, and all class probabilities.

        Args:
            crop: Cleaned RGB crop array (np.ndarray) or PIL Image.
            candidate_labels: Optional custom label prompt list.

        Returns:
            Dict[str, Any]:
                - 'predicted_label' (str): Top predicted category string.
                - 'confidence_score' (float): Softmax probability [0.0, 1.0].
                - 'all_scores' (Dict[str, float]): Class probability breakdown.
        """
        if self.model is None or self.preprocess is None or self.tokenizer is None:
            self.load_model()

        labels = candidate_labels or self.region_labels
        if not labels:
            return {
                "predicted_label": "architectural_component",
                "confidence_score": 1.0,
                "all_scores": {},
            }

        # Convert numpy array to PIL Image if necessary
        if isinstance(crop, np.ndarray):
            if crop.size == 0:
                return {
                    "predicted_label": labels[0],
                    "confidence_score": 0.0,
                    "all_scores": {l: 0.0 for l in labels},
                }
            if crop.dtype != np.uint8:
                crop = np.clip(crop, 0, 255).astype(np.uint8)
            pil_img = Image.fromarray(crop)
        elif isinstance(crop, Image.Image):
            pil_img = crop
        else:
            raise TypeError(f"Unsupported crop image type: {type(crop)}")

        # Transform and batch image tensor
        image_tensor = self.preprocess(pil_img).unsqueeze(0).to(self.device)
        text_tokens = self.tokenizer(labels).to(self.device)

        with torch.no_grad():
            image_features = self.model.encode_image(image_tensor)
            text_features = self.model.encode_text(text_tokens)

            # L2 Normalization of embeddings
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)

            # Cosine similarity and Softmax distribution
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            probs = similarity.squeeze(0).cpu().numpy()

        top_idx = int(np.argmax(probs))
        predicted_label = labels[top_idx]
        confidence_score = float(probs[top_idx])

        all_scores = {labels[i]: round(float(probs[i]), 4) for i in range(len(labels))}

        return {
            "predicted_label": predicted_label,
            "confidence_score": round(confidence_score, 4),
            "all_scores": all_scores,
        }

    def classify_masked_region(
        self,
        image: Union[Image.Image, np.ndarray],
        mask: np.ndarray,
        candidate_labels: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Convenience method returning class probability dictionary for a masked region."""
        if isinstance(image, Image.Image):
            img_arr = np.array(image)
        else:
            img_arr = image

        # Apply mask and compute crop
        masked = img_arr.copy()
        if len(masked.shape) == 3:
            masked[~mask] = 0
        else:
            masked[~mask] = 0

        y_idx, x_idx = np.where(mask)
        if len(y_idx) > 0 and len(x_idx) > 0:
            crop = masked[np.min(y_idx) : np.max(y_idx) + 1, np.min(x_idx) : np.max(x_idx) + 1]
        else:
            crop = masked

        res = self.classify_crop(crop, candidate_labels=candidate_labels)
        return res["all_scores"]

    def classify_masks(
        self,
        image: np.ndarray,
        masks: List[Dict[str, Any]],
        sam_segmenter: Any,
        candidate_labels: Optional[List[str]] = None,
        min_confidence: float = 0.10,
    ) -> List[Dict[str, Any]]:
        """Classify a list of SAM masks, filtering out non-structural and negative elements.

        Args:
            image: Source photo array.
            masks: List of SAM mask dictionaries from SAMSegmenter.generate_masks().
            sam_segmenter: Instance of SAMSegmenter for clean padded cropping.
            candidate_labels: Optional class label list override.
            min_confidence: Minimum confidence threshold to retain classification.

        Returns:
            List[Dict[str, Any]]: List of valid architectural component detections:
                - 'bbox' (List[int]): [x, y, w, h] bounding box.
                - 'region_type' (str): Classified architectural label.
                - 'confidence_score' (float): CLIP classification confidence.
                - 'all_scores' (Dict[str, float]): Class probability breakdown.
        """
        if image is None or image.size == 0 or not masks:
            return []

        classified_regions: List[Dict[str, Any]] = []

        for mask_dict in masks:
            # 1. Obtain clean, letterboxed RGB crop from SAMSegmenter
            crop = sam_segmenter.clip_and_clean_mask(image, mask_dict)

            # 2. Classify crop via OpenCLIP
            classification = self.classify_crop(crop, candidate_labels=candidate_labels)
            label = classification["predicted_label"]
            confidence = classification["confidence_score"]

            # 3. Filter out negative / transient non-structural classes
            if self.is_negative_label(label):
                logger.debug(f"Filtered out negative non-structural mask: '{label}' (conf={confidence:.2f})")
                continue

            if confidence < min_confidence:
                continue

            # Extract integer bounding box
            raw_bbox = mask_dict.get("bbox")
            if raw_bbox is not None and len(raw_bbox) == 4:
                bbox = [int(round(coord)) for coord in raw_bbox]
            else:
                # Fallback to computing bbox from mask array
                seg = mask_dict.get("segmentation")
                if seg is not None:
                    y_idx, x_idx = np.where(seg)
                    if len(y_idx) > 0 and len(x_idx) > 0:
                        min_x, max_x = int(np.min(x_idx)), int(np.max(x_idx))
                        min_y, max_y = int(np.min(y_idx)), int(np.max(y_idx))
                        bbox = [min_x, min_y, max_x - min_x + 1, max_y - min_y + 1]
                    else:
                        bbox = [0, 0, image.shape[1], image.shape[0]]
                else:
                    bbox = [0, 0, image.shape[1], image.shape[0]]

            classified_regions.append(
                {
                    "bbox": bbox,
                    "region_type": label,
                    "confidence_score": confidence,
                    "all_scores": classification["all_scores"],
                }
            )

        logger.info(
            f"Classified {len(classified_regions)} valid structural regions from {len(masks)} candidate masks"
        )
        return classified_regions
