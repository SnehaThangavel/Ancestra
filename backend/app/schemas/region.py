"""Pydantic schemas for Architectural Regions."""

import uuid
from datetime import datetime
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, ConfigDict, Field


class RegionBase(BaseModel):
    monument_id: uuid.UUID = Field(..., description="ID of the parent monument")
    name: str = Field(..., description="Name of the architectural region", min_length=2, max_length=128)
    category: Optional[str] = Field("facade", description="Structural type: facade, pillar, vimana, arch, dome, frieze")
    image_url: Optional[str] = Field(None, description="Regional detail photo URL")
    bounding_box: Optional[Any] = Field(None, description="Bounding coordinates [x, y, w, h] or polygon")
    reference_features: Optional[Dict[str, Any]] = Field(None, description="Visual descriptors / embeddings")


class RegionCreate(RegionBase):
    importance: Optional[str] = "Primary Sanctum Superstructure"


class RegionUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    bounding_box: Optional[Any] = None
    reference_features: Optional[Dict[str, Any]] = None
    importance: Optional[str] = None


class RegionResponse(RegionBase):
    id: uuid.UUID
    code: Optional[str] = None
    site_name: Optional[str] = None
    image: Optional[str] = None
    importance: Optional[str] = "Primary Sanctum Superstructure"
    condition: str = "MONITOR"
    risk_level: str = "MEDIUM"
    damage_score: Optional[int] = 0
    structural_health_index: Optional[float] = 1.0
    last_assessment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
