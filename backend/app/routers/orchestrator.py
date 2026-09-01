"""FastAPI router for Module 6 (Work Order Orchestration & Evidence Logs)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.orchestrator import WorkOrderCreate, WorkOrderResponse, EvidenceLogResponse

router = APIRouter(prefix="/orchestrator", tags=["Orchestration & Work Orders"])


@router.post("/work-orders", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_work_order(payload: WorkOrderCreate, db: Session = Depends(get_db)):
    """Dispatch prioritized conservation work order based on multi-criteria urgency score."""
    pass


@router.get("/work-orders", response_model=List[WorkOrderResponse])
async def list_work_orders(db: Session = Depends(get_db)):
    """List all pending and active conservation work orders."""
    pass


@router.get("/work-orders/{work_order_id}/evidence", response_model=List[EvidenceLogResponse])
async def get_work_order_evidence(work_order_id: int, db: Session = Depends(get_db)):
    """Retrieve immutable SHA-256 hash-chained audit evidence log for a work order."""
    pass
