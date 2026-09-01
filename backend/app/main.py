"""FastAPI application entrypoint for Ancestra Heritage Structural Monitoring Backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import (
    ingestion_router,
    consensus_router,
    validation_router,
    temporal_router,
    orchestrator_router,
)
from app.utils.logging import setup_logging

# Initialize logging
setup_logging()

# Create DB tables if dev/sqlite
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SESCI Architecture for Crowdsourced Monument Structural Monitoring",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register SESCI Module Routers
app.include_router(ingestion_router, prefix=settings.API_V1_STR)
app.include_router(consensus_router, prefix=settings.API_V1_STR)
app.include_router(validation_router, prefix=settings.API_V1_STR)
app.include_router(temporal_router, prefix=settings.API_V1_STR)
app.include_router(orchestrator_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
async def root_health_check():
    """Root health check endpoint."""
    return {
        "status": "healthy",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENV,
    }
