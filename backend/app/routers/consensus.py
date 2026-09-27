"""FastAPI router for Module 3 (Consensus State & Baseline Pointer Management)."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.observation import Observation
from app.models.region import Region
from app.auth.dependencies import get_current_user
from app.modules.consensus_memory import get_consensus_memory
from app.schemas.consensus import (
    ConsensusUpdateRequest,
    ConsensusResetRequest,
    ConsensusStateResponse,
)

router = APIRouter(prefix="/consensus", tags=["Consensus Memory"])

# Shared Module 3 service instance
consensus_service = get_consensus_memory()


@router.get(
    "/{region_id}",
    response_model=ConsensusStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current active baseline state and pointer for a region",
)
def get_region_consensus(
    region_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsensusStateResponse:
    """Retrieve the active consensus version, baseline observation ID, and latest observation pointer for a region."""
    try:
        reg_uuid = uuid.UUID(str(region_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid region UUID format: '{region_id}'",
        )

    active_state = consensus_service.get_active_consensus_state(reg_uuid, db=db)
    if not active_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No consensus state found for region '{region_id}'.",
        )

    return active_state


@router.get(
    "/{region_id}/history",
    response_model=List[ConsensusStateResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve all baseline version history for a region (post-restoration tracking)",
)
def get_region_consensus_history(
    region_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ConsensusStateResponse]:
    """Retrieve all historical consensus baseline versions and restoration reset records for a region."""
    try:
        reg_uuid = uuid.UUID(str(region_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid region UUID format: '{region_id}'",
        )

    history = consensus_service.get_consensus_history(reg_uuid, db=db)
    return history


@router.post(
    "/{region_id}/reset-baseline",
    response_model=ConsensusStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Create a new baseline version after verified physical restoration/repair",
)
def reset_region_baseline(
    region_id: str,
    payload: ConsensusResetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsensusStateResponse:
    """Trigger an explicit restoration reset establishing a new baseline version and resetting baseline reference pointer."""
    try:
        reg_uuid = uuid.UUID(str(region_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid region UUID format: '{region_id}'",
        )

    # Verify region exists in database
    region = db.query(Region).filter(Region.id == reg_uuid).first()
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region '{region_id}' not found.",
        )

    new_version_state = consensus_service.reset_baseline(
        region_id=reg_uuid,
        reason=payload.reason,
        baseline_observation_id=payload.baseline_observation_id,
        db=db,
    )
    return new_version_state


@router.post(
    "/{region_id}/reset",
    response_model=ConsensusStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Alias for reset-baseline",
)
def reset_region_consensus_alias(
    region_id: str,
    payload: ConsensusResetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsensusStateResponse:
    """Alias for reset-baseline for backward compatibility."""
    return reset_region_baseline(
        region_id=region_id,
        payload=payload,
        db=db,
        current_user=current_user,
    )


@router.post(
    "/record-observation",
    response_model=ConsensusStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Record observation to update latest observation pointer",
)
def record_observation_pointer(
    payload: ConsensusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsensusStateResponse:
    """Update regional consensus memory with a confirmed observation pointer."""
    try:
        obs_uuid = uuid.UUID(str(payload.observation_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid observation UUID format: '{payload.observation_id}'",
        )

    observation = db.query(Observation).filter(Observation.id == obs_uuid).first()
    if not observation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation '{payload.observation_id}' not found.",
        )

    if payload.region_id:
        try:
            observation.region_id = uuid.UUID(str(payload.region_id))
        except (ValueError, AttributeError):
            pass

    if observation.region_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Observation does not have an associated region_id.",
        )

    updated_state = consensus_service.process_observation(observation, db=db)
    if not updated_state:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update consensus memory state pointer.",
        )

    return updated_state


@router.post(
    "/update",
    response_model=ConsensusStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Alias for record-observation",
)
def update_region_consensus_alias(
    payload: ConsensusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsensusStateResponse:
    """Alias for record-observation for backward compatibility."""
    return record_observation_pointer(
        payload=payload,
        db=db,
        current_user=current_user,
    )
