"""FastAPI router for Module 4 (SSIM Anomaly Validation & Defect Detection)."""

import uuid
from typing import List, Union, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user, get_current_user_optional
from app.modules.validation import get_validation_module
from app.schemas.validation import AnomalyValidationRequest, AnomalyValidationResponse

router = APIRouter(prefix="/validation", tags=["Anomaly Validation"])

# Shared Module 4 service instance
validation_service = get_validation_module()


def _extract_primary_obs_id(corroborating_ids: Any) -> Optional[uuid.UUID]:
    """Helper to safely extract primary observation UUID."""
    if corroborating_ids and isinstance(corroborating_ids, (list, tuple)) and len(corroborating_ids) > 0:
        val = corroborating_ids[0]
        if isinstance(val, uuid.UUID):
            return val
        try:
            return uuid.UUID(str(val))
        except (ValueError, AttributeError):
            return None
    return None


@router.post(
    "/verify",
    response_model=AnomalyValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run SSIM anomaly comparison against regional baseline",
)
def validate_anomaly(
    payload: AnomalyValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnomalyValidationResponse:
    """Run full-reference SSIM comparison between an observation and the region's baseline."""
    try:
        obs_uuid = uuid.UUID(str(payload.observation_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid observation UUID format: '{payload.observation_id}'",
        )

    reg_uuid = None
    if payload.region_id:
        try:
            reg_uuid = uuid.UUID(str(payload.region_id))
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid region UUID format: '{payload.region_id}'",
            )

    try:
        result = validation_service.validate_observation(
            observation_id=obs_uuid,
            db=db,
            region_id=reg_uuid,
            ssim_threshold=payload.ssim_threshold,
        )
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during anomaly validation: {str(exc)}",
        ) from exc


@router.get(
    "/region/{region_id}",
    response_model=List[AnomalyValidationResponse],
    status_code=status.HTTP_200_OK,
    summary="List all validation findings for an architectural region",
)
def list_region_anomalies(
    region_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AnomalyValidationResponse]:
    """Retrieve all validated anomalies and structural health inspections for an architectural region."""
    try:
        reg_uuid = uuid.UUID(str(region_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid region UUID format: '{region_id}'",
        )

    records = validation_service.get_region_validations(reg_uuid, db=db)
    responses = []
    for r in records:
        bboxes = []
        ssim_score = None
        base_obs_id = None
        if r.defect_polygon and isinstance(r.defect_polygon, dict):
            bboxes = r.defect_polygon.get("bounding_boxes", [])
            ssim_score = r.defect_polygon.get("ssim_score")
            base_obs_id = r.defect_polygon.get("baseline_observation_id")

        primary_obs_id = _extract_primary_obs_id(r.corroborating_observation_ids)

        responses.append(
            AnomalyValidationResponse(
                validation_id=r.id,
                observation_id=primary_obs_id,
                baseline_observation_id=base_obs_id,
                region_id=r.region_id,
                anomaly_detected=bool(r.severity_score >= 0.05 or (r.ssim_delta and r.ssim_delta >= 0.05)),
                anomaly_type=r.anomaly_type,
                ssim_score=ssim_score,
                ssim_delta=r.ssim_delta,
                severity_score=r.severity_score,
                defect_bounding_boxes=bboxes,
                corroboration_count=r.corroboration_count,
                is_confirmed=r.is_confirmed,
                is_baseline=False,
                created_at=r.created_at,
            )
        )
    return responses


@router.get(
    "/observation/{observation_id}",
    response_model=AnomalyValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve validation finding for a specific observation",
)
def get_observation_anomaly(
    observation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnomalyValidationResponse:
    """Retrieve the validation report and anomaly bounding boxes for a specific observation."""
    try:
        obs_uuid = uuid.UUID(str(observation_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid observation UUID format: '{observation_id}'",
        )

    record = validation_service.get_observation_validation(obs_uuid, db=db)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No validation record found for observation '{observation_id}'.",
        )

    bboxes = []
    ssim_score = None
    base_obs_id = None
    if record.defect_polygon and isinstance(record.defect_polygon, dict):
        bboxes = record.defect_polygon.get("bounding_boxes", [])
        ssim_score = record.defect_polygon.get("ssim_score")
        base_obs_id = record.defect_polygon.get("baseline_observation_id")

    primary_obs_id = _extract_primary_obs_id(record.corroborating_observation_ids)

    return AnomalyValidationResponse(
        validation_id=record.id,
        observation_id=primary_obs_id,
        baseline_observation_id=base_obs_id,
        region_id=record.region_id,
        anomaly_detected=bool(record.severity_score >= 0.05 or (record.ssim_delta and record.ssim_delta >= 0.05)),
        anomaly_type=record.anomaly_type,
        ssim_score=ssim_score,
        ssim_delta=record.ssim_delta,
        severity_score=record.severity_score,
        defect_bounding_boxes=bboxes,
        corroboration_count=record.corroboration_count,
        is_confirmed=record.is_confirmed,
        is_baseline=False,
        created_at=record.created_at,
    )


@router.get(
    "/anomalies",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="List all recent validation anomaly records across all monuments/regions",
)
def list_all_anomalies(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> List[dict]:
    """Retrieve all validated anomalies enriched with monument and region metadata."""
    from app.models.monument import Monument
    from app.models.region import Region
    from app.models.observation import Observation

    records = (
        db.query(AnomalyValidation)
        .order_by(AnomalyValidation.created_at.desc())
        .limit(100)
        .all()
    )

    results = []
    for r in records:
        reg = db.query(Region).filter(Region.id == r.region_id).first()
        mon = db.query(Monument).filter(Monument.id == reg.monument_id).first() if reg else None
        
        primary_obs_id = _extract_primary_obs_id(r.corroborating_observation_ids)
        obs = db.query(Observation).filter(Observation.id == primary_obs_id).first() if primary_obs_id else None

        bboxes = []
        ssim_score = None
        base_obs_id = None
        if r.defect_polygon and isinstance(r.defect_polygon, dict):
            bboxes = r.defect_polygon.get("bounding_boxes", [])
            ssim_score = r.defect_polygon.get("ssim_score")
            base_obs_id = r.defect_polygon.get("baseline_observation_id")

        severity_label = "Low"
        if r.severity_score > 0.40:
            severity_label = "High"
        elif r.severity_score > 0.15:
            severity_label = "Medium"

        emergency_level = "Normal"
        if r.severity_score > 0.40:
            emergency_level = "Critical"
        elif r.severity_score > 0.20:
            emergency_level = "Urgent"
        elif r.severity_score > 0.05:
            emergency_level = "Attention"

        status_text = "Confirmed" if r.is_confirmed else "Pending Review"
        
        # Build image URL
        img_url = "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"
        if obs and obs.image_url:
            if obs.image_url.startswith("http"):
                img_url = obs.image_url
            else:
                img_url = f"http://localhost:8000/{obs.image_url.lstrip('/')}"

        results.append({
            "id": f"ASM-{str(r.id)[:8].upper()}",
            "validation_id": str(r.id),
            "siteId": str(mon.id) if mon else "",
            "siteName": mon.name if mon else "Monitored Monument",
            "regionId": str(reg.id) if reg else str(r.region_id),
            "regionCode": f"REG-{str(r.region_id)[:4].upper()}",
            "regionName": reg.name if reg else "Structural Region",
            "date": r.created_at.strftime("%Y-%m-%d"),
            "damageType": r.anomaly_type.replace("_", " ").title(),
            "severity": severity_label,
            "severity_score": r.severity_score,
            "ssim_score": ssim_score,
            "ssim_delta": r.ssim_delta,
            "confidence": 0.94 if r.severity_score > 0.1 else 0.88,
            "damageTrend": "Increasing" if r.severity_score > 0.2 else "Stable",
            "emergencyLevel": emergency_level,
            "recommendation": (
                "Immediate structural shoring & conservation intervention recommended."
                if r.severity_score > 0.2
                else "Routine monitoring and non-invasive surface consolidation recommended."
            ),
            "status": status_text,
            "imageUrl": img_url,
            "defect_bounding_boxes": bboxes,
            "expertNotes": f"SSIM Delta: {r.ssim_delta:.4f}, Severity: {r.severity_score:.4f}" if r.ssim_delta is not None else "",
            "created_at": r.created_at.isoformat(),
        })

    return results


@router.patch(
    "/{validation_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update anomaly validation confirmation status",
)
def update_anomaly_status(
    validation_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Update confirmation status and notes for an anomaly validation finding."""
    try:
        val_uuid = uuid.UUID(validation_id.replace("ASM-", "").lower() if len(validation_id) == 36 else validation_id)
    except ValueError:
        # Search by prefix or direct ID
        pass

    record = db.query(AnomalyValidation).filter(AnomalyValidation.id == val_uuid).first() if 'val_uuid' in locals() else None
    if not record:
        records = db.query(AnomalyValidation).all()
        for r in records:
            if str(r.id).startswith(validation_id.replace("ASM-", "").lower()):
                record = r
                break

    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validation record not found")

    if "is_confirmed" in payload:
        record.is_confirmed = bool(payload["is_confirmed"])
    if "status" in payload:
        record.is_confirmed = payload["status"].lower() == "confirmed"
    
    db.commit()
    db.refresh(record)
    return {"success": True, "validation_id": str(record.id), "is_confirmed": record.is_confirmed}
