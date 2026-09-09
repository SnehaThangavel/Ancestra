"""Pydantic schemas for photo ingestion, EXIF parsing, and quality assessment."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class EXIFMetadata(BaseModel):
    """Extracted camera and environmental metadata from EXIF."""

    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    iso: Optional[int] = None
    exposure_time: Optional[float] = None
    focal_length: Optional[float] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_altitude: Optional[float] = None
    timestamp: Optional[datetime] = None


class ImageIngestionRequest(BaseModel):
    """Request schema for initiating crowdsourced photo ingestion."""

    monument_id: Union[uuid.UUID, str] = Field(..., description="Unique monument identifier")
    user_id: Optional[str] = Field(None, description="Crowdsource contributor identifier")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image data")
    image_url: Optional[str] = Field(None, description="Direct URL of the uploaded image")


class ImageIngestionResponse(BaseModel):
    """Response schema for processed image ingestion."""

    observation_id: Union[uuid.UUID, int, str]
    monument_id: Union[uuid.UUID, str]
    is_valid_quality: bool
    blur_score: float
    glare_score: float
    resolution_w: int
    resolution_h: int
    exif: Optional[EXIFMetadata] = None
    matched_region_id: Optional[Union[uuid.UUID, int, str]] = None
    registration_confidence: Optional[float] = None
    created_at: datetime
