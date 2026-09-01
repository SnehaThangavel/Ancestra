"""Pydantic schemas for the six-factor reliability computation."""

from typing import Dict, Any
from pydantic import BaseModel, Field


class ReliabilityFactors(BaseModel):
    """Breakdown of the six patent reliability factors."""

    sensor_quality: float = Field(..., ge=0.0, le=1.0, description="Sensor resolution & optics fidelity")
    lighting_condition: float = Field(..., ge=0.0, le=1.0, description="Illumination and glare factor")
    vantage_perspective: float = Field(..., ge=0.0, le=1.0, description="Vantage angle orthogonality")
    contributor_reputation: float = Field(..., ge=0.0, le=1.0, description="Crowd contributor reliability history")
    temporal_proximity: float = Field(..., ge=0.0, le=1.0, description="Decay weight over time")
    registration_precision: float = Field(..., ge=0.0, le=1.0, description="ORB/homography alignment score")


class ReliabilityScoreRequest(BaseModel):
    """Request schema to compute composite reliability."""

    observation_id: int
    custom_weights: Dict[str, float] = Field(default_factory=dict)


class ReliabilityScoreResponse(BaseModel):
    """Response schema containing composite reliability score and factor weights."""

    observation_id: int
    composite_reliability: float = Field(..., ge=0.0, le=1.0)
    factors: ReliabilityFactors
