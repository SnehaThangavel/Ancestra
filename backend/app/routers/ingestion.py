"""FastAPI router for Module 1 (Photo Ingestion & Quality Assessment)."""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.ingestion import ImageIngestionResponse

router = APIRouter(prefix="/ingestion", tags=["Ingestion & Registration"])


@router.post("/upload", response_model=ImageIngestionResponse, status_code=status.HTTP_201_CREATED)
async def upload_observation(
    monument_id: str = Form(...),
    user_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload crowdsourced monument photo for quality triage, EXIF extraction, and ORB registration."""
    pass
