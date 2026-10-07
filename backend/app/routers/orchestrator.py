"""FastAPI router for Module 6 (Work Order Orchestration & Hash-Chained Evidence Logs)."""

import uuid
from typing import List, Union, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.work_order import WorkOrder, EvidenceLog
from app.models.validation import AnomalyValidation
from app.auth.dependencies import get_current_user
from app.modules.orchestrator import get_orchestrator_module
from app.schemas.orchestrator import (
    UrgencyScoreResponse,
    WorkOrderCreate,
    WorkOrderResponse,
    EvidenceLogResponse,
    EvidenceChainVerificationResponse,
)

router = APIRouter(prefix="/orchestrator", tags=["Orchestration & Work Orders"])
orchestrator_service = get_orchestrator_module()


@router.get(
    "/urgency/{region_id}",
    response_model=UrgencyScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate multi-criteria urgency score for a region",
)
def get_region_urgency(
    region_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UrgencyScoreResponse:
    """Compute composite multi-criteria urgency score combining severity, health deficit, and temporal trend."""
    try:
        reg_uuid = uuid.UUID(str(region_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid region UUID format: '{region_id}'",
        )

    try:
        urgency_data = orchestrator_service.compute_urgency_score(region_id=reg_uuid, db=db)
        return UrgencyScoreResponse(**urgency_data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute urgency score: {str(exc)}",
        ) from exc


@router.post(
    "/work-orders",
    response_model=WorkOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Dispatch a conservation work order",
)
def create_work_order(
    payload: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkOrderResponse:
    """Dispatch a prioritized conservation work order based on multi-criteria urgency score and log Genesis audit block."""
    target_region_id = payload.region_id

    # If only validation_id is passed, look up the region
    if target_region_id is None and payload.validation_id is not None:
        try:
            val_uuid = uuid.UUID(str(payload.validation_id))
            val = db.query(AnomalyValidation).filter(AnomalyValidation.id == val_uuid).first()
            if not val:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Anomaly validation with ID '{payload.validation_id}' not found.",
                )
            target_region_id = val.region_id
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid validation UUID format: '{payload.validation_id}'",
            )

    if not target_region_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'region_id' or 'validation_id' must be provided to create a work order.",
        )

    try:
        custom_action = payload.recommended_action or payload.description
        work_order = orchestrator_service.generate_work_order(
            region_id=target_region_id,
            db=db,
            description=custom_action,
            validation_id=payload.validation_id,
            assigned_team=payload.assigned_team,
        )

        # Retrieve urgency level
        level = "medium"
        if work_order.urgency_index >= 0.70:
            level = "critical"
        elif work_order.urgency_index >= 0.45:
            level = "high"
        elif work_order.urgency_index < 0.20:
            level = "low"

        return WorkOrderResponse(
            id=work_order.id,
            validation_id=work_order.validation_id,
            region_id=target_region_id,
            urgency_score=work_order.urgency_index,
            urgency_level=level,
            status=work_order.status,
            assigned_team=work_order.assigned_team,
            recommended_action=work_order.recommended_action,
            created_at=work_order.created_at,
            updated_at=work_order.updated_at,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create work order: {str(exc)}",
        ) from exc


@router.get(
    "/work-orders",
    response_model=List[WorkOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="List all conservation work orders",
)
def list_work_orders(
    region_id: Optional[str] = Query(None, description="Filter work orders by architectural region ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter work orders by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[WorkOrderResponse]:
    """Retrieve all pending and active conservation work orders with optional filtering."""
    query = db.query(WorkOrder)

    if region_id:
        try:
            reg_uuid = uuid.UUID(str(region_id))
            query = query.join(AnomalyValidation, WorkOrder.validation_id == AnomalyValidation.id).filter(
                AnomalyValidation.region_id == reg_uuid
            )
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid region UUID: '{region_id}'")

    if status_filter:
        query = query.filter(WorkOrder.status == status_filter.lower())

    orders = query.order_by(WorkOrder.created_at.desc()).all()

    responses = []
    for wo in orders:
        val = db.query(AnomalyValidation).filter(AnomalyValidation.id == wo.validation_id).first()
        level = "medium"
        if wo.urgency_index >= 0.70:
            level = "critical"
        elif wo.urgency_index >= 0.45:
            level = "high"
        elif wo.urgency_index < 0.20:
            level = "low"

        responses.append(
            WorkOrderResponse(
                id=wo.id,
                validation_id=wo.validation_id,
                region_id=val.region_id if val else None,
                urgency_score=wo.urgency_index,
                urgency_level=level,
                status=wo.status,
                assigned_team=wo.assigned_team,
                recommended_action=wo.recommended_action,
                created_at=wo.created_at,
                updated_at=wo.updated_at,
            )
        )
    return responses


@router.get(
    "/work-orders/{work_order_id}",
    response_model=WorkOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get work order by ID",
)
def get_work_order(
    work_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkOrderResponse:
    """Retrieve single work order by UUID."""
    try:
        wo_uuid = uuid.UUID(str(work_order_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid work order UUID: '{work_order_id}'")

    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_uuid).first()
    if not wo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Work order '{work_order_id}' not found.")

    val = db.query(AnomalyValidation).filter(AnomalyValidation.id == wo.validation_id).first()
    level = "medium"
    if wo.urgency_index >= 0.70:
        level = "critical"
    elif wo.urgency_index >= 0.45:
        level = "high"
    elif wo.urgency_index < 0.20:
        level = "low"

    return WorkOrderResponse(
        id=wo.id,
        validation_id=wo.validation_id,
        region_id=val.region_id if val else None,
        urgency_score=wo.urgency_index,
        urgency_level=level,
        status=wo.status,
        assigned_team=wo.assigned_team,
        recommended_action=wo.recommended_action,
        created_at=wo.created_at,
        updated_at=wo.updated_at,
    )


@router.get(
    "/work-orders/{work_order_id}/evidence",
    response_model=List[EvidenceLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve audit trail for a work order",
)
def get_work_order_evidence(
    work_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[EvidenceLogResponse]:
    """Retrieve immutable SHA-256 hash-chained audit evidence log blocks for a work order."""
    try:
        wo_uuid = uuid.UUID(str(work_order_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid work order UUID: '{work_order_id}'")

    logs = (
        db.query(EvidenceLog)
        .filter(EvidenceLog.work_order_id == wo_uuid)
        .order_by(EvidenceLog.block_index.asc())
        .all()
    )

    return [
        EvidenceLogResponse(
            id=log.id,
            work_order_id=log.work_order_id,
            block_index=log.block_index,
            previous_hash=log.previous_hash,
            current_hash=log.current_hash,
            payload=log.payload if isinstance(log.payload, dict) else {},
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get(
    "/evidence-log/{region_id}",
    response_model=List[EvidenceLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve all evidence logs for an architectural region",
)
def get_region_evidence_logs(
    region_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[EvidenceLogResponse]:
    """Retrieve all evidence log blocks across all work orders attached to a specific region."""
    try:
        reg_uuid = uuid.UUID(str(region_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid region UUID: '{region_id}'")

    logs = (
        db.query(EvidenceLog)
        .join(WorkOrder, EvidenceLog.work_order_id == WorkOrder.id)
        .join(AnomalyValidation, WorkOrder.validation_id == AnomalyValidation.id)
        .filter(AnomalyValidation.region_id == reg_uuid)
        .order_by(EvidenceLog.created_at.desc())
        .all()
    )

    return [
        EvidenceLogResponse(
            id=log.id,
            work_order_id=log.work_order_id,
            block_index=log.block_index,
            previous_hash=log.previous_hash,
            current_hash=log.current_hash,
            payload=log.payload if isinstance(log.payload, dict) else {},
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get(
    "/work-orders/{work_order_id}/verify-chain",
    response_model=EvidenceChainVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify cryptographic SHA-256 hash-chain integrity",
)
def verify_work_order_evidence_chain(
    work_order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvidenceChainVerificationResponse:
    """Verify that no evidence log block has been tampered with or modified."""
    try:
        wo_uuid = uuid.UUID(str(work_order_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid work order UUID: '{work_order_id}'")

    verification = orchestrator_service.verify_evidence_chain(work_order_id=wo_uuid, db=db)
    return EvidenceChainVerificationResponse(**verification)
