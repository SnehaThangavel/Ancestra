"""Pydantic schemas for consensus memory running updates and state retrieval."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class ConsensusUpdateRequest(BaseModel):
    """Request schema for updating regional consensus state with a new observation."""

    region_id: Union[uuid.UUID, int, str]
    observation_id: Union[uuid.UUID, int, str]
    reliability_weight: float = Field(..., ge=0.0, le=1.0)


class ConsensusStateResponse(BaseModel):
    """Response schema for regional consensus state."""

    region_id: Union[uuid.UUID, int, str]
    version: int
    structural_health_index: float = Field(..., ge=0.0, le=1.0)
    cumulative_reliability: float
    observation_count: int
    last_updated: datetime
    state_vector_summary: Optional[Dict[str, Any]] = None
