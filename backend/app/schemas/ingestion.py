"""Pydantic schemas for photo ingestion, EXIF parsing, region suggestion, and quality assessment."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Union, List
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
    """Request schema for initiating photo ingestion."""

    monument_id: Union[uuid.UUID, str] = Field(..., description="Unique monument identifier")
    region_id: Optional[Union[uuid.UUID, str]] = Field(None, description="Explicit region identifier confirmed by expert")
    user_id: Optional[str] = Field(None, description="Expert or contributor identifier")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image data")
    image_url: Optional[str] = Field(None, description="Direct URL of the uploaded image")


class RegionItem(BaseModel):
    """Summary of an architectural region available for selection."""

    id: Union[uuid.UUID, str]
    name: str
    category: Optional[str] = None
    bounding_box: Optional[Any] = None


class RegionSuggestionResponse(BaseModel):
    """Response schema for AI-assisted region suggestion."""

    monument_id: Union[uuid.UUID, str]
    suggested_region_id: Optional[Union[uuid.UUID, str]] = None
    suggested_region_name: Optional[str] = None
    confidence_score: float = Field(0.0, description="Confidence score of AI region suggestion in [0, 1]")
    detected_category: Optional[str] = None
    bounding_box: Optional[List[int]] = None
    available_regions: List[RegionItem] = Field(default_factory=list, description="All existing regions for dropdown confirmation")


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
    registration_success: Optional[bool] = False
    registration_confidence: Optional[float] = None
    is_baseline: Optional[bool] = False
    created_at: datetime
