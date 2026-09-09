"""Pydantic schemas for consensus memory running updates and state retrieval (SESCI Module 3)."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict


class ConsensusUpdateRequest(BaseModel):
    """Request schema for updating regional consensus state with an observation."""

    observation_id: Union[uuid.UUID, str] = Field(..., description="Observation ID to incorporate into consensus memory")
    region_id: Optional[Union[uuid.UUID, str]] = Field(None, description="Optional region ID override")
    reliability_weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Optional reliability score override")


class ConsensusResetRequest(BaseModel):
    """Request schema for creating a new consensus state version (major repair/reset)."""

    reason: Optional[str] = Field(
        None,
        description="Reason for resetting consensus version (e.g., major repair/restoration completed)",
    )


class ConsensusStateResponse(BaseModel):
    """Response schema for regional consensus state."""

    id: Optional[Union[uuid.UUID, str]] = None
    region_id: Union[uuid.UUID, str]
    version: int
    structural_health_index: float = Field(..., ge=0.0, le=1.0)
    cumulative_reliability: float
    observation_count: int
    last_updated_by_observation_id: Optional[Union[uuid.UUID, str]] = None
    reset_reason: Optional[str] = None
    consensus_tensor: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, extra="allow")

    @property
    def last_updated(self) -> Optional[datetime]:
        """Backward compatibility alias for updated_at."""
        return self.updated_at

    @property
    def state_vector_summary(self) -> Optional[Dict[str, Any]]:
        """Backward compatibility alias for consensus_tensor."""
        return self.consensus_tensor

