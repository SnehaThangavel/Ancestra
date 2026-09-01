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

    # Database Configuration (SQLite default for dev, PostgreSQL in prod)
    DATABASE_URL: str = "sqlite:///./ancestra.db"

    # AI Model Settings (SAM & CLIP)
    SAM_CHECKPOINT_PATH: str = "app/ai/model_weights/sam_vit_h_4b8939.pth"
    SAM_MODEL_TYPE: str = "vit_h"
    CLIP_MODEL_NAME: str = "ViT-B-32"
    CLIP_PRETRAINED: str = "laion2b_s34b_b79k"
    DEVICE: str = "cpu"

    # Storage & Uploads
    UPLOAD_DIR: str = "./uploads"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
