"""Application configuration and environment settings."""

from typing import Dict, List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings and environment variables."""

    # Project Information
    PROJECT_NAME: str = "Ancestra"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    ENV: str = "development"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:8000", "*"]
    FRONTEND_URL: str = "http://localhost:5173"

    # Database Configuration (PostgreSQL)
    DATABASE_URL: str = "postgresql://ancestra_user:ancestra_password@localhost:5432/ancestra_db"
    TEST_DATABASE_URL: str = "postgresql://ancestra_user:ancestra_password@localhost:5432/ancestra_test_db"

    # Google OAuth Configuration (loaded from environment / .env)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_ALLOWED_DOMAIN: Optional[str] = None

    # JWT Authentication Settings
    JWT_SECRET_KEY: str = "ancestra_super_secret_jwt_key_development_2026_change_in_prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI Model Settings (SAM & CLIP)
    SAM_CHECKPOINT_PATH: str = "app/ai/model_weights/sam_vit_b_01ec64.pth"
    SAM_MODEL_TYPE: str = "vit_b"
    SAM_POINTS_PER_SIDE: int = 32
    SAM_PRED_IOU_THRESH: float = 0.86
    SAM_STABILITY_SCORE_THRESH: float = 0.92
    SAM_MIN_MASK_REGION_AREA: int = 500
    MIN_MASK_AREA_RATIO: float = 0.005

    CLIP_MODEL_NAME: str = "ViT-B-32"
    CLIP_PRETRAINED: str = "laion2b_s34b_b79k"
    CLIP_REGION_LABELS: List[str] = [
        "stone pillar column",
        "structural dome roof",
        "arched doorway entrance",
        "masonry wall facade",
        "carved stone sculpture",
        "ancient stone inscription",
        "decorative carved frieze",
        "weathered foundation base",
        "person or tourist",
        "vegetation or trees",
        "clear or cloudy sky",
        "vehicle or modern object",
    ]
    CLIP_NEGATIVE_LABELS: List[str] = [
        "person or tourist",
        "vegetation or trees",
        "clear or cloudy sky",
        "vehicle or modern object",
    ]
    DEVICE: str = "cpu"
    USE_AI_SEGMENTATION: bool = True
    REGION_IOU_THRESHOLD: float = 0.5

    # Storage & Uploads
    UPLOAD_DIR: str = "./uploads"
    LOG_LEVEL: str = "INFO"

    # Image Quality & Ingestion Thresholds
    MIN_IMAGE_WIDTH: int = 400
    MIN_IMAGE_HEIGHT: int = 300
    BLUR_LAPLACIAN_MIN_VAR: float = 80.0
    GLARE_MAX_RATIO: float = 0.25
    MIN_QUALITY_THRESHOLD: float = 0.35
    ORB_MAX_FEATURES: int = 2000
    MIN_MATCH_COUNT: int = 8
    RANSAC_REPROJ_THRESHOLD: float = 5.0

    # Reliability Engine Settings (Module 2)
    RELIABILITY_TEMPORAL_HALF_LIFE_DAYS: float = 180.0
    RELIABILITY_WEIGHTS: Dict[str, float] = {
        "image_quality": 0.25,
        "geometric_consistency": 0.20,
        "viewpoint_diversity": 0.10,
        "temporal_relevance": 0.15,
        "environmental_similarity": 0.10,
        "agreement": 0.20,
    }

    @field_validator("RELIABILITY_WEIGHTS")
    @classmethod
    def validate_reliability_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate that reliability factor weights sum approximately to 1.0."""
        required_factors = {
            "image_quality",
            "geometric_consistency",
            "viewpoint_diversity",
            "temporal_relevance",
            "environmental_similarity",
            "agreement",
        }
        missing = required_factors - set(v.keys())
        if missing:
            raise ValueError(f"Missing required reliability factor weight(s): {missing}")
        total = sum(v.values())
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"Reliability weights must sum to 1.0, got {total}")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
