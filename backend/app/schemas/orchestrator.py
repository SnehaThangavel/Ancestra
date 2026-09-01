"""Pydantic schemas for work orders, urgency scoring, and hash-chained evidence logs."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WorkOrderCreate(BaseModel):
    """Request schema for dispatching a conservation work order."""

    validation_id: int
    assigned_team: Optional[str] = None
    recommended_action: str


class WorkOrderResponse(BaseModel):
    """Response schema for conservation work order."""

    id: int
    validation_id: int
    urgency_score: float
    status: str
    assigned_team: Optional[str] = None
    recommended_action: str
    created_at: datetime
    updated_at: datetime


class EvidenceLogResponse(BaseModel):
    """Response schema for immutable hash-chained audit log entry."""

    id: int
    work_order_id: int
    previous_hash: str
    current_hash: str
    payload_snapshot: Dict[str, Any]
    timestamp: datetime
