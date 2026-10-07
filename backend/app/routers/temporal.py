"""FastAPI router for Module 5 (Temporal Deterioration Trend Forecasting)."""

from typing import Optional, Union
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.modules.temporal_evolution import TemporalEvolutionModule, get_temporal_evolution
from app.schemas.temporal import TemporalTrendRequest, TemporalTrendResponse

router = APIRouter(prefix="/temporal", tags=["Temporal Evolution"])
temporal_service = get_temporal_evolution()


@router.get(
    "/region/{region_id}",
    response_model=TemporalTrendResponse,
    status_code=status.HTTP_200_OK,
    summary="Get temporal deterioration trend for a region",
)
def get_region_trend(
    region_id: str,
    forecast_days: int = Query(default=90, ge=1, le=365),
    critical_threshold: float = Query(default=0.40, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemporalTrendResponse:
    """Retrieve temporal deterioration rate, trajectory classification, and future health projection for a specific region."""
    try:
        reg_uuid = uuid.UUID(str(region_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid region UUID format: '{region_id}'",
        )

    try:
        projection = temporal_service.project_future_health(
            region_id=reg_uuid,
            db=db,
            horizon_days=forecast_days,
            critical_threshold=critical_threshold,
        )

        trend_status = projection.get("trend_status", "calculated")
        return TemporalTrendResponse(
            region_id=str(reg_uuid),
            status=trend_status,
            trend_classification=projection.get("trend_classification", "stable"),
            projection_confidence=projection.get("projection_confidence", "low"),
            confidence_note=projection.get("confidence_note"),
            deterioration_rate_per_day=projection.get("deterioration_rate_per_day", 0.0),
            current_health_index=projection.get("current_health_index", 1.0),
            projected_health_index_90d=projection.get("projected_health_index", 1.0),
            time_to_critical_threshold_days=projection.get("time_to_critical_threshold_days"),
            is_projection_estimate=True,
            projection_label=projection.get("projection_label"),
            historical_series=projection.get("historical_series", []),
            record_count=len(projection.get("historical_series", [])),
            span_days=projection.get("span_days", 0.0),
            message=projection.get("message"),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while computing temporal deterioration trend: {str(exc)}",
        ) from exc


@router.post("/trend", response_model=TemporalTrendResponse, status_code=status.HTTP_200_OK)
def get_deterioration_trend(
    payload: TemporalTrendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemporalTrendResponse:
    """Compute deterioration velocity and forecast time-to-critical degradation horizon for an architectural region."""
    try:
        projection = temporal_service.project_future_health(
            region_id=payload.region_id,
            db=db,
            horizon_days=payload.forecast_days,
            critical_threshold=payload.critical_threshold,
        )

        trend_status = projection.get("trend_status", "calculated")
        return TemporalTrendResponse(
            region_id=payload.region_id,
            status=trend_status,
            trend_classification=projection.get("trend_classification", "stable"),
            projection_confidence=projection.get("projection_confidence", "low"),
            confidence_note=projection.get("confidence_note"),
            deterioration_rate_per_day=projection.get("deterioration_rate_per_day", 0.0),
            current_health_index=projection.get("current_health_index", 1.0),
            projected_health_index_90d=projection.get("projected_health_index", 1.0),
            time_to_critical_threshold_days=projection.get("time_to_critical_threshold_days"),
            is_projection_estimate=True,
            projection_label=projection.get("projection_label"),
            historical_series=projection.get("historical_series", []),
            record_count=len(projection.get("historical_series", [])),
            span_days=projection.get("span_days", 0.0),
            message=projection.get("message"),
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while computing temporal deterioration trend: {str(exc)}",
        ) from exc
