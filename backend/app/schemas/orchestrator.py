"""Pydantic schemas for work orders, urgency scoring, and hash-chained evidence logs."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class WorkOrderCreate(BaseModel):
    """Request schema for dispatching a conservation work order."""

    validation_id: Union[uuid.UUID, int, str]
    assigned_team: Optional[str] = None
    recommended_action: str


class WorkOrderResponse(BaseModel):
    """Response schema for conservation work order."""

    id: Union[uuid.UUID, int, str]
    validation_id: Union[uuid.UUID, int, str]
    urgency_score: float
    status: str
    assigned_team: Optional[str] = None
    recommended_action: str
    created_at: datetime
    updated_at: datetime


class EvidenceLogResponse(BaseModel):
    """Response schema for immutable hash-chained audit log entry."""

    id: Union[uuid.UUID, int, str]
    work_order_id: Union[uuid.UUID, int, str]
    previous_hash: str
    current_hash: str
    payload_snapshot: Dict[str, Any]
    timestamp: datetime
