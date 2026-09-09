"""FastAPI router for Module 2 (Six-Factor Reliability Coefficient Engine)."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.observation import Observation
from app.auth.dependencies import get_current_user
from app.modules.reliability_engine import ReliabilityEngineModule, get_reliability_engine
from app.schemas.reliability import (
    ReliabilityScoreRequest,
    ReliabilityScoreResponse,
    ReliabilityFactors,
)

router = APIRouter(prefix="/reliability", tags=["Reliability Engine"])

# Shared Module 2 service instance
reliability_service = get_reliability_engine()


@router.post(
    "/score/{observation_id}",
    response_model=ReliabilityScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute dynamic reliability coefficient for an observation",
)
def score_observation(
    observation_id: str,
    request: Optional[ReliabilityScoreRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReliabilityScoreResponse:
    """Compute and persist the six-factor composite reliability coefficient R_i for an observation.

    Args:
        observation_id: UUID or identifier of the Observation to score.
        request: Optional request payload specifying custom factor weight overrides.
        db: SQLAlchemy database session.
        current_user: Authenticated user principal.

    Returns:
        ReliabilityScoreResponse: Composite reliability score and breakdown across all 6 factors.
    """
    try:
        obs_uuid = uuid.UUID(str(observation_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid observation UUID format: '{observation_id}'",
        )

    observation = db.query(Observation).filter(Observation.id == obs_uuid).first()
    if not observation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation with ID '{observation_id}' not found.",
        )

    custom_weights = request.custom_weights if request and request.custom_weights else None

    try:
        result = reliability_service.compute_reliability(
            observation=observation,
            db=db,
            custom_weights=custom_weights,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute reliability score: {str(exc)}",
        ) from exc

    return ReliabilityScoreResponse(
        observation_id=observation.id,
        reliability_score=result["reliability_score"],
        factors=ReliabilityFactors(**result["reliability_factors"]),
    )
