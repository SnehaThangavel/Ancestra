"""FastAPI router for Monument (Heritage Site) entity management."""

import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.monument import Monument
from app.models.region import Region
from app.models.observation import Observation
from app.models.consensus_state import ConsensusState
from app.auth.dependencies import get_current_user, get_current_user_optional
from app.schemas.monument import MonumentCreate, MonumentUpdate, MonumentResponse

router = APIRouter(prefix="/monuments", tags=["Monuments & Heritage Sites"])


def _map_monument_response(mon: Monument, db: Session) -> MonumentResponse:
    # Calculate regions count
    regions_count = db.query(func.count(Region.id)).filter(Region.monument_id == mon.id).scalar() or 0
    
    # Check latest observation date
    latest_obs = (
        db.query(Observation)
        .filter(Observation.monument_id == mon.id)
        .order_by(Observation.created_at.desc())
        .first()
    )
    last_assessment = latest_obs.created_at.strftime("%Y-%m-%d") if latest_obs else mon.created_at.strftime("%Y-%m-%d")
    
    # Calculate overall health/status from consensus states
    reg_ids = [r.id for r in db.query(Region.id).filter(Region.monument_id == mon.id).all()]
    status_label = "MONITOR"
    if reg_ids:
        min_health = (
            db.query(func.min(ConsensusState.structural_health_index))
            .filter(ConsensusState.region_id.in_(reg_ids))
            .scalar()
        )
        if min_health is not None:
            if min_health < 0.70:
                status_label = "CRITICAL"
            elif min_health < 0.90:
                status_label = "MONITOR"
            else:
                status_label = "STABLE"

    code = f"HST-{str(mon.id)[:4].upper()}"
    
    # Default image covers based on monument name
    image_url = None
    lower_name = mon.name.lower()
    if "shore" in lower_name:
        image_url = "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"
    elif "brihadisvara" in lower_name or "thanjavur" in lower_name:
        image_url = "https://images.unsplash.com/photo-1600100397608-f090742f4949?auto=format&fit=crop&q=80&w=800"
    elif "hampi" in lower_name:
        image_url = "https://images.unsplash.com/photo-1627894099419-f5ebba5e3f42?auto=format&fit=crop&q=80&w=800"
    elif "konark" in lower_name:
        image_url = "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?auto=format&fit=crop&q=80&w=800"
    else:
        image_url = "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?auto=format&fit=crop&q=80&w=800"

    return MonumentResponse(
        id=mon.id,
        code=code,
        name=mon.name,
        location_name=mon.location_name or "India",
        latitude=mon.latitude,
        longitude=mon.longitude,
        heritage_status=mon.heritage_status or "UNESCO World Heritage Site",
        importance_tier=mon.importance_tier or 1,
        regions_count=regions_count,
        status=status_label,
        material="Granite & Dressed Freestone Blocks",
        circle="ASI Directorate",
        description="",
        image=image_url,
        last_assessment=last_assessment,
        created_at=mon.created_at,
        updated_at=mon.updated_at,
    )


@router.get("", response_model=List[MonumentResponse], summary="List all monitored heritage monuments")
def list_monuments(
    search: Optional[str] = Query(None, description="Search query by name or location"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> List[MonumentResponse]:
    """Retrieve all monitored monument entities stored in the database."""
    query = db.query(Monument)
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            (Monument.name.ilike(search_fmt)) | (Monument.location_name.ilike(search_fmt))
        )
    monuments = query.order_by(Monument.name.asc()).all()
    return [_map_monument_response(m, db) for m in monuments]


@router.post("", response_model=MonumentResponse, status_code=status.HTTP_201_CREATED, summary="Create a new heritage monument")
def create_monument(
    payload: MonumentCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> MonumentResponse:
    """Create a new heritage monument record."""
    mon = Monument(
        id=uuid.uuid4(),
        name=payload.name,
        location_name=payload.location_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        heritage_status=payload.heritage_status,
        importance_tier=payload.importance_tier,
    )
    db.add(mon)
    db.commit()
    db.refresh(mon)
    return _map_monument_response(mon, db)


@router.get("/{monument_id}", response_model=MonumentResponse, summary="Get monument details")
def get_monument(
    monument_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> MonumentResponse:
    """Get single monument record by ID."""
    try:
        mon_uuid = uuid.UUID(monument_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid monument UUID")
    
    mon = db.query(Monument).filter(Monument.id == mon_uuid).first()
    if not mon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monument not found")
    return _map_monument_response(mon, db)


@router.put("/{monument_id}", response_model=MonumentResponse, summary="Update a heritage monument")
def update_monument(
    monument_id: str,
    payload: MonumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MonumentResponse:
    """Update monument metadata."""
    try:
        mon_uuid = uuid.UUID(monument_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid monument UUID")
    
    mon = db.query(Monument).filter(Monument.id == mon_uuid).first()
    if not mon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monument not found")
    
    if payload.name is not None:
        mon.name = payload.name
    if payload.location_name is not None:
        mon.location_name = payload.location_name
    if payload.latitude is not None:
        mon.latitude = payload.latitude
    if payload.longitude is not None:
        mon.longitude = payload.longitude
    if payload.heritage_status is not None:
        mon.heritage_status = payload.heritage_status
    if payload.importance_tier is not None:
        mon.importance_tier = payload.importance_tier
    
    mon.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(mon)
    return _map_monument_response(mon, db)


@router.delete("/{monument_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a heritage monument")
def delete_monument(
    monument_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a monument and all associated regions/observations."""
    try:
        mon_uuid = uuid.UUID(monument_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid monument UUID")
    
    mon = db.query(Monument).filter(Monument.id == mon_uuid).first()
    if not mon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monument not found")
    
    db.delete(mon)
    db.commit()
    return None
