"""Pydantic schemas for SSIM anomaly detection and defect validation (SESCI Module 4)."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict


class AnomalyValidationRequest(BaseModel):
    """Request schema to trigger anomaly validation against regional baseline."""

    observation_id: Union[uuid.UUID, str] = Field(..., description="Target observation ID to analyze")
    region_id: Optional[Union[uuid.UUID, str]] = Field(None, description="Optional region ID override")
    ssim_threshold: float = Field(default=0.85, ge=0.0, le=1.0, description="SSIM threshold below which anomalies are flagged")


class AnomalyValidationResponse(BaseModel):
    """Response schema for validated structural anomalies."""

    validation_id: Optional[Union[uuid.UUID, str]] = None
    observation_id: Optional[Union[uuid.UUID, str]] = None
    baseline_observation_id: Optional[Union[uuid.UUID, str]] = None
    region_id: Union[uuid.UUID, str]
    anomaly_detected: bool
    anomaly_type: Optional[str] = None
    ssim_score: Optional[float] = None
    ssim_delta: Optional[float] = None
    severity_score: float = Field(0.0, ge=0.0, le=1.0)
    defect_bounding_boxes: Optional[List[List[int]]] = None
    corroboration_count: int = 1
    is_confirmed: bool = True
    is_baseline: bool = False
    message: Optional[str] = None
    defect_mask_url: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, extra="allow")
