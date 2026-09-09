"""Tests for Reliability Pydantic schemas (SESCI Module 2)."""

import uuid
import pytest
from pydantic import ValidationError
from app.schemas.reliability import (
    ReliabilityScoreRequest,
    ReliabilityScoreResponse,
    ReliabilityFactors,
)


def test_reliability_factors_valid() -> None:
    """Test valid instantiation of ReliabilityFactors."""
    factors = ReliabilityFactors(
        image_quality=0.85,
        geometric_consistency=0.72,
        viewpoint_diversity=0.60,
        temporal_relevance=0.95,
        environmental_similarity=0.80,
        agreement=0.90,
    )
    assert factors.image_quality == 0.85
    assert factors.geometric_consistency == 0.72
    assert factors.viewpoint_diversity == 0.60
    assert factors.temporal_relevance == 0.95
    assert factors.environmental_similarity == 0.80
    assert factors.agreement == 0.90


def test_reliability_factors_out_of_bounds() -> None:
    """Test validation errors on out-of-bound reliability factor values."""
    with pytest.raises(ValidationError):
        ReliabilityFactors(
            image_quality=1.5,  # > 1.0
            geometric_consistency=0.5,
            viewpoint_diversity=0.5,
            temporal_relevance=0.5,
            environmental_similarity=0.5,
            agreement=0.5,
        )

    with pytest.raises(ValidationError):
        ReliabilityFactors(
            image_quality=0.5,
            geometric_consistency=-0.1,  # < 0.0
            viewpoint_diversity=0.5,
            temporal_relevance=0.5,
            environmental_similarity=0.5,
            agreement=0.5,
        )


def test_reliability_score_response() -> None:
    """Test ReliabilityScoreResponse serialization."""
    obs_id = uuid.uuid4()
    factors = ReliabilityFactors(
        image_quality=0.9,
        geometric_consistency=0.8,
        viewpoint_diversity=0.7,
        temporal_relevance=0.95,
        environmental_similarity=0.85,
        agreement=1.0,
    )
    resp = ReliabilityScoreResponse(
        observation_id=obs_id,
        reliability_score=0.885,
        factors=factors,
    )
    assert resp.observation_id == obs_id
    assert resp.reliability_score == 0.885
    assert resp.factors.agreement == 1.0
