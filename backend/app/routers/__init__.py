"""FastAPI router package."""

from app.routers.auth import router as auth_router
from app.routers.ingestion import router as ingestion_router
from app.routers.reliability import router as reliability_router
from app.routers.consensus import router as consensus_router
from app.routers.validation import router as validation_router
from app.routers.temporal import router as temporal_router
from app.routers.orchestrator import router as orchestrator_router

__all__ = [
    "auth_router",
    "ingestion_router",
    "reliability_router",
    "consensus_router",
    "validation_router",
    "temporal_router",
    "orchestrator_router",
]

