"""Tests for OpenCLIP region classifier."""

from unittest.mock import MagicMock
import pytest
import numpy as np
import torch
from PIL import Image

from app.ai.region_classifier import CLIPRegionClassifier
from app.ai.sam_segmenter import SAMSegmenter


@pytest.fixture
def region_classifier() -> CLIPRegionClassifier:
    """Fixture providing initialized CLIPRegionClassifier without downloading weights."""
    return CLIPRegionClassifier(
        model_name="ViT-B-32",
        device="cpu",
        auto_load=False,
    )


def test_region_classifier_init(region_classifier: CLIPRegionClassifier) -> None:
    """Test CLIPRegionClassifier initialization and label categories."""
    assert region_classifier.model_name == "ViT-B-32"
    assert region_classifier.device == "cpu"
    assert "stone pillar column" in region_classifier.region_labels
    assert "structural dome roof" in region_classifier.region_labels
    assert "person or tourist" in region_classifier.negative_labels


def test_is_negative_label(region_classifier: CLIPRegionClassifier) -> None:
    """Test filtering logic for non-structural / transient objects."""
    # Negative labels
    assert region_classifier.is_negative_label("person or tourist") is True
    assert region_classifier.is_negative_label("vegetation or trees") is True
    assert region_classifier.is_negative_label("clear or cloudy sky") is True
    assert region_classifier.is_negative_label("vehicle or modern object") is True
    assert region_classifier.is_negative_label("tourist with camera") is True
    assert region_classifier.is_negative_label("green tree branch") is True

    # Structural labels
    assert region_classifier.is_negative_label("stone pillar column") is False
    assert region_classifier.is_negative_label("structural dome roof") is False
    assert region_classifier.is_negative_label("arched doorway entrance") is False
    assert region_classifier.is_negative_label("masonry wall facade") is False
    assert region_classifier.is_negative_label("ancient stone inscription") is False


def test_classify_crop_with_mocked_clip(region_classifier: CLIPRegionClassifier) -> None:
    """Test classify_crop output formatting, probabilities, and top prediction."""
    mock_model = MagicMock()
    mock_preprocess = MagicMock(return_value=torch.zeros((3, 224, 224)))
    mock_tokenizer = MagicMock(return_value=torch.zeros((len(region_classifier.region_labels), 77)))

    # Mock embeddings: give index 0 ("stone pillar column") the highest similarity
    num_labels = len(region_classifier.region_labels)
    img_feature = torch.zeros((1, 512))
    img_feature[0, 0] = 1.0

    text_features = torch.zeros((num_labels, 512))
    text_features[0, 0] = 1.0  # Index 0 has dot product 1.0
    for i in range(1, num_labels):
        text_features[i, i] = 0.2

    mock_model.encode_image.return_value = img_feature
    mock_model.encode_text.return_value = text_features

    region_classifier.model = mock_model
    region_classifier.preprocess = mock_preprocess
    region_classifier.tokenizer = mock_tokenizer

    dummy_crop = np.zeros((224, 224, 3), dtype=np.uint8)
    result = region_classifier.classify_crop(dummy_crop)

    assert result["predicted_label"] == "stone pillar column"
    assert result["confidence_score"] > 0.50
    assert len(result["all_scores"]) == num_labels
    assert "stone pillar column" in result["all_scores"]
    assert pytest.approx(sum(result["all_scores"].values()), 0.05) == 1.0


def test_classify_masks_filters_negative_classes() -> None:
    """Test classify_masks end-to-end: keeping structural regions and dropping negative classes."""
    classifier = CLIPRegionClassifier(device="cpu", auto_load=False)
    segmenter = SAMSegmenter(device="cpu", auto_load=False)

    img = np.zeros((400, 600, 3), dtype=np.uint8)

    # 2 masks: Mask 1 (pillar) and Mask 2 (person)
    mask_pillar = np.zeros((400, 600), dtype=bool)
    mask_pillar[50:350, 100:200] = True

    mask_person = np.zeros((400, 600), dtype=bool)
    mask_person[100:300, 400:500] = True

    masks = [
        {"segmentation": mask_pillar, "bbox": [100, 50, 100, 300]},
        {"segmentation": mask_person, "bbox": [400, 100, 100, 200]},
    ]

    # Mock classify_crop: return 'stone pillar column' for first crop and 'person or tourist' for second
    call_count = 0

    def mock_classify_crop(crop, candidate_labels=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {
                "predicted_label": "stone pillar column",
                "confidence_score": 0.88,
                "all_scores": {"stone pillar column": 0.88, "person or tourist": 0.02},
            }
        else:
            return {
                "predicted_label": "person or tourist",
                "confidence_score": 0.94,
                "all_scores": {"stone pillar column": 0.01, "person or tourist": 0.94},
            }

    classifier.classify_crop = mock_classify_crop

    results = classifier.classify_masks(img, masks, sam_segmenter=segmenter)

    # Only 1 structural region should be retained
    assert len(results) == 1
    assert results[0]["region_type"] == "stone pillar column"
    assert results[0]["bbox"] == [100, 50, 100, 300]
    assert results[0]["confidence_score"] == 0.88
