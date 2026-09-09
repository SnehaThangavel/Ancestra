"""Pydantic schemas for SSIM anomaly detection and consensus validation."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class AnomalyValidationRequest(BaseModel):
    """Request schema to trigger anomaly validation against regional consensus."""

    observation_id: Union[uuid.UUID, int, str]
    region_id: Union[uuid.UUID, int, str]
    ssim_threshold: float = Field(default=0.85, ge=0.0, le=1.0)


class AnomalyValidationResponse(BaseModel):
    """Response schema for validated structural anomalies."""

    validation_id: Union[uuid.UUID, int, str]
    region_id: Union[uuid.UUID, int, str]
    anomaly_detected: bool
    anomaly_type: Optional[str] = None
    ssim_delta: Optional[float] = None
    severity_score: float = Field(..., ge=0.0, le=1.0)
    corroboration_count: int
    is_confirmed: bool
    defect_mask_url: Optional[str] = None
    created_at: datetime
