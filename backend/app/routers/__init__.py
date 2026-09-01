"""FastAPI router package."""

from app.routers.ingestion import router as ingestion_router
from app.routers.consensus import router as consensus_router
from app.routers.validation import router as validation_router
from app.routers.temporal import router as temporal_router
from app.routers.orchestrator import router as orchestrator_router

__all__ = [
    "ingestion_router",
    "consensus_router",
    "validation_router",
    "temporal_router",
    "orchestrator_router",
]
