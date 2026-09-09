"""Pydantic schemas for the six-factor reliability computation (SESCI Module 2)."""

import uuid
from typing import Dict, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class ReliabilityFactors(BaseModel):
    """Breakdown of the six patent reliability factors R_i in [0, 1]."""

    image_quality: float = Field(
        ..., ge=0.0, le=1.0, description="Image sharpness, exposure, and resolution quality factor"
    )
    geometric_consistency: float = Field(
        ..., ge=0.0, le=1.0, description="ORB/RANSAC homography inlier ratio and feature registration precision"
    )
    viewpoint_diversity: float = Field(
        ..., ge=0.0, le=1.0, description="Viewing angle and vantage diversity relative to 90-day regional history"
    )
    temporal_relevance: float = Field(
        ..., ge=0.0, le=1.0, description="Exponential time decay weight based on observation age and half-life"
    )
    environmental_similarity: float = Field(
        ..., ge=0.0, le=1.0, description="Lighting and exposure consistency compared to regional historical norm"
    )
    agreement: float = Field(
        ..., ge=0.0, le=1.0, description="Structural agreement with regional consensus memory state"
    )

    model_config = ConfigDict(from_attributes=True, extra="allow")


class ReliabilityScoreRequest(BaseModel):
    """Request schema to compute composite reliability."""

    observation_id: Union[uuid.UUID, str]
    custom_weights: Optional[Dict[str, float]] = Field(default=None, description="Optional custom weight overrides")


class ReliabilityScoreResponse(BaseModel):
    """Response schema containing composite reliability score and factor breakdown."""

    observation_id: Union[uuid.UUID, str]
    reliability_score: float = Field(..., ge=0.0, le=1.0, description="Composite reliability coefficient R_i in [0, 1]")
    factors: ReliabilityFactors

    model_config = ConfigDict(from_attributes=True)

