"""AI Foundation Models package (Segment Anything Model & OpenCLIP).

Provides singleton factory access for heavy vision foundation models (SAM & OpenCLIP).
"""

from typing import Optional
from app.ai.sam_segmenter import SAMSegmenter
from app.ai.region_classifier import CLIPRegionClassifier

_sam_segmenter_instance: Optional[SAMSegmenter] = None
_region_classifier_instance: Optional[CLIPRegionClassifier] = None


def get_sam_segmenter(auto_load: bool = False) -> SAMSegmenter:
    """Get or create singleton instance of SAMSegmenter."""
    global _sam_segmenter_instance
    if _sam_segmenter_instance is None:
        _sam_segmenter_instance = SAMSegmenter(auto_load=auto_load)
    elif auto_load and _sam_segmenter_instance.model is None:
        _sam_segmenter_instance.load_model()
    return _sam_segmenter_instance


def get_region_classifier(auto_load: bool = False) -> CLIPRegionClassifier:
    """Get or create singleton instance of CLIPRegionClassifier."""
    global _region_classifier_instance
    if _region_classifier_instance is None:
        _region_classifier_instance = CLIPRegionClassifier(auto_load=auto_load)
    elif auto_load and _region_classifier_instance.model is None:
        _region_classifier_instance.load_model()
    return _region_classifier_instance


__all__ = [
    "SAMSegmenter",
    "CLIPRegionClassifier",
    "get_sam_segmenter",
    "get_region_classifier",
]
