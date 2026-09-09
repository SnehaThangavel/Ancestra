"""FastAPI router for Module 6 (Work Order Orchestration & Evidence Logs)."""

import uuid
from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.schemas.orchestrator import WorkOrderCreate, WorkOrderResponse, EvidenceLogResponse

router = APIRouter(prefix="/orchestrator", tags=["Orchestration & Work Orders"])


@router.post("/work-orders", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_work_order(
    payload: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dispatch prioritized conservation work order based on multi-criteria urgency score."""
    pass


@router.get("/work-orders", response_model=List[WorkOrderResponse])
async def list_work_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all pending and active conservation work orders."""
    pass


@router.get("/work-orders/{work_order_id}/evidence", response_model=List[EvidenceLogResponse])
async def get_work_order_evidence(
    work_order_id: Union[uuid.UUID, int, str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve immutable SHA-256 hash-chained audit evidence log for a work order."""
    pass
