"""FastAPI application entrypoint for Ancestra Heritage Structural Monitoring Backend."""

import os
import sys

# Ensure backend root is on sys.path even when running directly
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.routers import (
    auth_router,
    ingestion_router,
    reliability_router,
    consensus_router,
    validation_router,
    temporal_router,
    orchestrator_router,
    monuments_router,
    regions_router,
)
from app.utils.logging import setup_logging

# Initialize logging
setup_logging()

# Create DB tables if dev/test
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SESCI Architecture for Crowdsourced Monument Structural Monitoring",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Mount static uploads directory for serving uploaded observation images
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# SessionMiddleware required by Authlib for transient OAuth CSRF state verification
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET_KEY,
    max_age=3600,
)

# CORS middleware configuration allowing frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Authentication and SESCI Module Routers
app.include_router(auth_router)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(monuments_router, prefix=settings.API_V1_STR)
app.include_router(regions_router, prefix=settings.API_V1_STR)
app.include_router(ingestion_router, prefix=settings.API_V1_STR)
app.include_router(reliability_router, prefix=settings.API_V1_STR)
app.include_router(consensus_router, prefix=settings.API_V1_STR)
app.include_router(validation_router, prefix=settings.API_V1_STR)
app.include_router(temporal_router, prefix=settings.API_V1_STR)
app.include_router(orchestrator_router, prefix=settings.API_V1_STR)


@app.get(f"{settings.API_V1_STR}/docs", include_in_schema=False)
async def api_v1_docs_redirect():
    """Redirect /api/v1/docs to /docs for developer convenience."""
    return RedirectResponse(url="/docs")


@app.get(f"{settings.API_V1_STR}/openapi.json", include_in_schema=False)
async def api_v1_openapi_redirect():
    """Redirect /api/v1/openapi.json to /openapi.json for compatibility."""
    return RedirectResponse(url="/openapi.json")


@app.get("/", tags=["Health"])
async def root_health_check():
    """Root health check endpoint."""
    return {
        "status": "healthy",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENV,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info",
    )
