"""Application configuration and environment settings."""

from typing import List
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
    CORS_ORIGINS: List[str] = ["*"]

    # Database Configuration (PostgreSQL)
    DATABASE_URL: str = "postgresql://ancestra_user:ancestra_password@localhost:5432/ancestra_db"
    TEST_DATABASE_URL: str = "postgresql://ancestra_user:ancestra_password@localhost:5432/ancestra_test_db"

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
