"""Pydantic schemas for temporal deterioration trends and forecasting."""

import uuid
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field


class TemporalDataPoint(BaseModel):
    """Single temporal observation data point for a region."""

    timestamp: datetime
    health_index: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    anomaly_severity: float = Field(default=0.0, ge=0.0, le=1.0)
    ssim_delta: Optional[float] = None
    anomaly_type: Optional[str] = None


class TemporalTrendRequest(BaseModel):
    """Request schema for temporal analysis and forecasting."""

    region_id: Union[uuid.UUID, int, str]
    forecast_days: int = Field(default=90, ge=1, le=365)
    critical_threshold: Optional[float] = Field(default=0.40, ge=0.0, le=1.0)


class TemporalTrendResponse(BaseModel):
    """Response schema containing trend analysis, classification, confidence grading, and future health projection."""

    region_id: Union[uuid.UUID, int, str]
    status: str = Field(default="calculated", description="'calculated' or 'insufficient_data'")
    trend_classification: str = Field(default="stable", description="'increasing', 'decreasing', or 'stable'")
    projection_confidence: str = Field(default="low", description="'low', 'medium', or 'high'")
    confidence_note: Optional[str] = None
    deterioration_rate_per_day: float
    current_health_index: Optional[float] = 1.0
    projected_health_index_90d: float
    time_to_critical_threshold_days: Optional[float] = None
    is_projection_estimate: bool = True
    projection_label: Optional[str] = "Linear forecast estimate based on validated anomaly history"
    historical_series: List[Dict[str, Any]] = Field(default_factory=list)
    record_count: int = 0
    span_days: Optional[float] = 0.0
    active_restoration_version: int = 1
    message: Optional[str] = None
