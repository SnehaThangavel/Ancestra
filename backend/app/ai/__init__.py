"""AI Foundation Models package (Segment Anything Model & OpenCLIP)."""

from app.ai.sam_segmenter import SAMSegmenter
from app.ai.region_classifier import CLIPRegionClassifier

__all__ = ["SAMSegmenter", "CLIPRegionClassifier"]
