"""Pydantic schemas for Monuments (Heritage Sites)."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class MonumentBase(BaseModel):
    name: str = Field(..., description="Name of the heritage monument", min_length=2, max_length=255)
    location_name: Optional[str] = Field(None, description="City, district, or state of the monument")
    latitude: Optional[float] = Field(None, description="GPS latitude coordinate")
    longitude: Optional[float] = Field(None, description="GPS longitude coordinate")
    heritage_status: Optional[str] = Field("UNESCO World Heritage Site", description="Heritage classification")
    importance_tier: int = Field(1, ge=1, le=5, description="Tier 1 (highest) to Tier 5")
    image_url: Optional[str] = Field(None, description="High-resolution imagery asset URL")


class MonumentCreate(MonumentBase):
    pass


class MonumentUpdate(BaseModel):
    name: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    heritage_status: Optional[str] = None
    importance_tier: Optional[int] = None
    image_url: Optional[str] = None


class MonumentResponse(MonumentBase):
    id: uuid.UUID
    code: Optional[str] = None
    regions_count: int = 0
    status: str = "MONITOR"
    material: Optional[str] = "Granite & Dressed Freestone Blocks"
    circle: Optional[str] = "ASI Directorate"
    description: Optional[str] = ""
    image: Optional[str] = None
    last_assessment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
