"""FastAPI router for Module 3 (Consensus Memory State)."""

import uuid
from typing import Union
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.observation import Observation
from app.models.region import Region
from app.auth.dependencies import get_current_user
from app.modules.consensus_memory import ConsensusMemoryModule, get_consensus_memory
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
    summary="Retrieve current active consensus memory state for a region",
)
def get_region_consensus(
    region_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsensusStateResponse:
    """Retrieve the latest active consensus state, feature tensor, and health index for a region."""
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


@router.post(
    "/update",
    response_model=ConsensusStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Manually trigger consensus memory update with an observation",
)
def update_region_consensus(
    payload: ConsensusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsensusStateResponse:
    """Trigger reliability-weighted running update on regional consensus memory using an observation."""
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

    # Allow overriding region_id or reliability_weight if provided in request
    if payload.region_id:
        try:
            observation.region_id = uuid.UUID(str(payload.region_id))
        except (ValueError, AttributeError):
            pass

    if payload.reliability_weight is not None:
        observation.reliability_score = payload.reliability_weight

    if observation.region_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Observation does not have an associated region_id.",
        )

    updated_state = consensus_service.process_observation(observation, db=db)
    if not updated_state:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update consensus memory state.",
        )

    return updated_state


@router.post(
    "/{region_id}/reset",
    response_model=ConsensusStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Create a new consensus version after verified repair/restoration",
)
def reset_region_consensus(
    region_id: str,
    payload: ConsensusResetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsensusStateResponse:
    """Create a new incremented ConsensusState version, resetting cumulative reliability and baseline tensor."""
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

    new_version_state = consensus_service.create_new_consensus_version(
        region_id=reg_uuid,
        reason=payload.reason,
        db=db,
    )
    return new_version_state
