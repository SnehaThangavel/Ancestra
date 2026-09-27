"""Pydantic schemas for consensus baseline pointers, restoration resets, and state retrieval (SESCI Module 3)."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict


class ConsensusUpdateRequest(BaseModel):
    """Request schema for updating regional consensus pointer with a new observation."""

    observation_id: Union[uuid.UUID, str] = Field(..., description="Observation ID to record as latest regional observation")
    region_id: Optional[Union[uuid.UUID, str]] = Field(None, description="Optional region ID override")
    reliability_weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Optional legacy weight field")


class ConsensusResetRequest(BaseModel):
    """Request schema for creating a new consensus state baseline version (major restoration/repair)."""

    reason: Optional[str] = Field(
        "Restoration work completed",
        description="Reason for resetting consensus baseline version",
    )
    baseline_observation_id: Optional[Union[uuid.UUID, str]] = Field(
        None,
        description="Optional observation ID to set as the initial baseline for the new version",
    )


class ConsensusStateResponse(BaseModel):
    """Response schema for regional consensus state and baseline pointer."""

    id: Optional[Union[uuid.UUID, str]] = None
    region_id: Union[uuid.UUID, str]
    version: int
    baseline_observation_id: Optional[Union[uuid.UUID, str]] = None
    last_observation_id: Optional[Union[uuid.UUID, str]] = None
    last_updated_by_observation_id: Optional[Union[uuid.UUID, str]] = None
    structural_health_index: float = Field(1.0, ge=0.0, le=1.0)
    observation_count: int = 0
    cumulative_reliability: Optional[float] = 0.0
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


