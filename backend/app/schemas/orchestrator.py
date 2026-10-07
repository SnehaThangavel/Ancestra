"""Pydantic schemas for work orders, urgency scoring, and hash-chained evidence logs."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class UrgencyScoreResponse(BaseModel):
    """Response schema for multi-criteria urgency score computation."""

    region_id: Union[uuid.UUID, str]
    region_name: str
    urgency_score: float = Field(..., ge=0.0, le=1.0, description="Composite urgency index in [0.0, 1.0]")
    urgency_level: str = Field(..., description="'low', 'medium', 'high', or 'critical'")
    latest_validation_id: Optional[Union[uuid.UUID, str]] = None
    latest_anomaly_type: Optional[str] = None
    severity_score: float = 0.0
    structural_health_index: float = 1.0
    health_deficit: float = 0.0
    trend_classification: str = "stable"
    deterioration_rate_per_day: float = 0.0
    trend_factor: float = 0.0
    rationale: str


class WorkOrderCreate(BaseModel):
    """Request schema for creating/dispatching a conservation work order."""

    region_id: Optional[Union[uuid.UUID, int, str]] = None
    validation_id: Optional[Union[uuid.UUID, int, str]] = None
    assigned_team: Optional[str] = None
    recommended_action: Optional[str] = None
    description: Optional[str] = None


class WorkOrderResponse(BaseModel):
    """Response schema for conservation work order."""

    id: Union[uuid.UUID, str]
    validation_id: Union[uuid.UUID, str]
    region_id: Optional[Union[uuid.UUID, str]] = None
    urgency_score: float
    urgency_level: Optional[str] = None
    status: str
    assigned_team: Optional[str] = None
    recommended_action: str
    created_at: datetime
    updated_at: datetime


class EvidenceLogResponse(BaseModel):
    """Response schema for immutable hash-chained audit log entry."""

    id: Union[uuid.UUID, str]
    work_order_id: Union[uuid.UUID, str]
    block_index: int
    previous_hash: str
    current_hash: str
    payload: Dict[str, Any]
    created_at: datetime


class EvidenceChainVerificationResponse(BaseModel):
    """Response schema for verifying cryptographic audit log integrity."""

    work_order_id: Union[uuid.UUID, str]
    is_valid: bool
    block_count: int
    genesis_hash: Optional[str] = None
    head_hash: Optional[str] = None
    tampered_block_index: Optional[int] = None
    error: Optional[str] = None
    message: str
