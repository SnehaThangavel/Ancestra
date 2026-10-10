"""FastAPI router for Architectural Region entity management."""

import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.monument import Monument
from app.models.region import Region
from app.models.observation import Observation
from app.models.consensus_state import ConsensusState
from app.models.validation import AnomalyValidation
from app.auth.dependencies import get_current_user, get_current_user_optional
from app.schemas.region import RegionCreate, RegionUpdate, RegionResponse

router = APIRouter(prefix="/regions", tags=["Architectural Regions"])


def _map_region_response(reg: Region, db: Session) -> RegionResponse:
    mon = db.query(Monument).filter(Monument.id == reg.monument_id).first()
    site_name = mon.name if mon else "Unknown Monument"
    
    # Check consensus state for health index
    cs = (
        db.query(ConsensusState)
        .filter(ConsensusState.region_id == reg.id)
        .order_by(ConsensusState.version.desc())
        .first()
    )
    health = cs.structural_health_index if cs else 1.0
    
    # Check latest observation date
    latest_obs = (
        db.query(Observation)
        .filter(Observation.region_id == reg.id)
        .order_by(Observation.created_at.desc())
        .first()
    )
    last_assessment = latest_obs.created_at.strftime("%Y-%m-%d") if latest_obs else reg.created_at.strftime("%Y-%m-%d")

    condition = "STABLE"
    risk_level = "LOW"
    damage_score = int((1.0 - health) * 100) if health is not None else 0
    if health is not None:
        if health < 0.70:
            condition = "CRITICAL"
            risk_level = "HIGH"
        elif health < 0.90:
            condition = "MONITOR"
            risk_level = "MEDIUM"
        else:
            condition = "STABLE"
            risk_level = "LOW"

    code = f"REG-{str(reg.id)[:4].upper()}"

    return RegionResponse(
        id=reg.id,
        monument_id=reg.monument_id,
        site_name=site_name,
        name=reg.name,
        category=reg.category or "facade",
        bounding_box=reg.bounding_box,
        image_url=reg.image_url,
        image=reg.image_url,
        reference_features=reg.reference_features,
        code=code,
        importance="Primary Structural Course",
        condition=condition,
        risk_level=risk_level,
        damage_score=damage_score,
        structural_health_index=health,
        last_assessment=last_assessment,
        created_at=reg.created_at,
        updated_at=reg.updated_at,
    )


@router.get("", response_model=List[RegionResponse], summary="List architectural regions")
def list_regions(
    monument_id: Optional[str] = Query(None, description="Filter regions by monument ID"),
    search: Optional[str] = Query(None, description="Search query by name"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> List[RegionResponse]:
    """Retrieve architectural regions, optionally filtered by monument ID."""
    query = db.query(Region)
    if monument_id:
        try:
            mon_uuid = uuid.UUID(monument_id)
            query = query.filter(Region.monument_id == mon_uuid)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid monument UUID")
    
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(Region.name.ilike(search_fmt))
        
    regions = query.order_by(Region.name.asc()).all()
    if not regions:
        return []

    # Batch fetch monuments
    monument_ids = {r.monument_id for r in regions if r.monument_id}
    monuments = db.query(Monument).filter(Monument.id.in_(monument_ids)).all() if monument_ids else []
    monument_map = {m.id: m.name for m in monuments}

    # Batch fetch latest consensus states
    region_ids = [r.id for r in regions]
    cs_records = (
        db.query(ConsensusState)
        .filter(ConsensusState.region_id.in_(region_ids))
        .order_by(ConsensusState.version.desc())
        .all()
    )
    cs_map = {}
    for cs in cs_records:
        if cs.region_id not in cs_map:
            cs_map[cs.region_id] = cs

    # Batch fetch latest observations
    obs_records = (
        db.query(Observation)
        .filter(Observation.region_id.in_(region_ids))
        .order_by(Observation.created_at.desc())
        .all()
    )
    obs_map = {}
    for obs in obs_records:
        if obs.region_id not in obs_map:
            obs_map[obs.region_id] = obs

    responses = []
    for reg in regions:
        site_name = monument_map.get(reg.monument_id, "Unknown Monument")
        cs = cs_map.get(reg.id)
        health = cs.structural_health_index if cs else 1.0
        
        latest_obs = obs_map.get(reg.id)
        last_assessment = latest_obs.created_at.strftime("%Y-%m-%d") if latest_obs else reg.created_at.strftime("%Y-%m-%d")

        condition = "STABLE"
        risk_level = "LOW"
        damage_score = int((1.0 - health) * 100) if health is not None else 0
        if health is not None:
            if health < 0.70:
                condition = "CRITICAL"
                risk_level = "HIGH"
            elif health < 0.90:
                condition = "MONITOR"
                risk_level = "MEDIUM"
            else:
                condition = "STABLE"
                risk_level = "LOW"

        code = f"REG-{str(reg.id)[:4].upper()}"

        responses.append(
            RegionResponse(
                id=reg.id,
                monument_id=reg.monument_id,
                site_name=site_name,
                name=reg.name,
                category=reg.category or "facade",
                image_url=reg.image_url,
                image=reg.image_url,
                bounding_box=reg.bounding_box,
                reference_features=reg.reference_features,
                code=code,
                importance="Primary Structural Course",
                condition=condition,
                risk_level=risk_level,
                damage_score=damage_score,
                structural_health_index=health,
                last_assessment=last_assessment,
                created_at=reg.created_at,
                updated_at=reg.updated_at,
            )
        )
    return responses


@router.post("", response_model=RegionResponse, status_code=status.HTTP_201_CREATED, summary="Create a new architectural region")
def create_region(
    payload: RegionCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> RegionResponse:
    """Create a new architectural region for a monument."""
    # Verify monument exists
    mon = db.query(Monument).filter(Monument.id == payload.monument_id).first()
    if not mon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monument not found")

    reg = Region(
        id=uuid.uuid4(),
        monument_id=payload.monument_id,
        name=payload.name,
        category=payload.category,
        bounding_box=payload.bounding_box,
        reference_features=payload.reference_features,
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return _map_region_response(reg, db)


@router.get("/{region_id}", response_model=RegionResponse, summary="Get region details")
def get_region(
    region_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> RegionResponse:
    """Get single architectural region record by ID."""
    try:
        reg_uuid = uuid.UUID(region_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid region UUID")
    
    reg = db.query(Region).filter(Region.id == reg_uuid).first()
    if not reg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    return _map_region_response(reg, db)


@router.put("/{region_id}", response_model=RegionResponse, summary="Update an architectural region")
def update_region(
    region_id: str,
    payload: RegionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RegionResponse:
    """Update region metadata."""
    try:
        reg_uuid = uuid.UUID(region_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid region UUID")
    
    reg = db.query(Region).filter(Region.id == reg_uuid).first()
    if not reg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    
    if payload.name is not None:
        reg.name = payload.name
    if payload.category is not None:
        reg.category = payload.category
    if payload.bounding_box is not None:
        reg.bounding_box = payload.bounding_box
    if payload.reference_features is not None:
        reg.reference_features = payload.reference_features
    
    reg.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(reg)
    return _map_region_response(reg, db)


@router.delete("/{region_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an architectural region")
def delete_region(
    region_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an architectural region and all associated observations."""
    try:
        reg_uuid = uuid.UUID(region_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid region UUID")
    
    reg = db.query(Region).filter(Region.id == reg_uuid).first()
    if not reg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    
    db.delete(reg)
    db.commit()
    return None
