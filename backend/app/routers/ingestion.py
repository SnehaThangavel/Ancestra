"""FastAPI router for Module 1 (Photo Ingestion & Quality Assessment)."""

from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.modules.ingestion import ImageIngestionModule
from app.schemas.ingestion import ImageIngestionResponse

router = APIRouter(prefix="/ingestion", tags=["Ingestion & Registration"])

# Shared Module 1 instance
ingestion_service = ImageIngestionModule()


@router.post("/upload", response_model=ImageIngestionResponse, status_code=status.HTTP_201_CREATED)
async def upload_observation(
    monument_id: str = Form(..., description="Unique monument identifier"),
    user_id: Optional[str] = Form(None, description="Crowdsource contributor ID"),
    file: UploadFile = File(..., description="Monument photo file"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload crowdsourced monument photo for quality triage, EXIF extraction, and ORB registration."""
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        effective_user = user_id or current_user.email

        response = ingestion_service.ingest(
            image_bytes=image_bytes,
            monument_id=monument_id,
            user_id=effective_user,
            db=db,
            image_url=file.filename,
        )
        return response
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the observation: {str(exc)}",
        ) from exc
