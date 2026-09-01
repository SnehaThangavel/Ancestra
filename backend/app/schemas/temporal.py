"""Pydantic schemas for temporal deterioration trends and forecasting."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TemporalDataPoint(BaseModel):
    """Single temporal observation data point for a region."""

    timestamp: datetime
    health_index: float = Field(..., ge=0.0, le=1.0)
    anomaly_severity: float = Field(default=0.0, ge=0.0, le=1.0)


class TemporalTrendRequest(BaseModel):
    """Request schema for temporal analysis and forecasting."""

    region_id: int
    forecast_days: int = Field(default=90, ge=1, le=365)


class TemporalTrendResponse(BaseModel):
    """Response schema containing trend analysis and deterioration velocity."""

    region_id: int
    deterioration_rate_per_day: float
    projected_health_index_90d: float
    time_to_critical_threshold_days: Optional[float] = None
    historical_series: List[TemporalDataPoint] = Field(default_factory=list)
