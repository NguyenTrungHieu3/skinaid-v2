from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from pathlib import Path
from typing import Optional
import os
import logging


class Settings(BaseSettings):
    # ==================== MODEL CONFIG ====================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    # ==================== APPLICATION ====================
    APP_NAME: str = "SkinAid AI Detection Service"
    APP_VERSION: str = "1.0.0"
    APP_ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # ==================== API ====================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_V1_PREFIX: str = "/api/v1"
    REQUEST_TIMEOUT: int = Field(default=10, ge=5, le=30)
    MAX_CONCURRENT_REQUESTS: int = Field(default=5, ge=1, le=50)

    # ==================== MODELS ====================
    DETECTION_MODEL_PATH: Path = Path("ai_ml/detection/models/best.pt")
    CLASSIFICATION_MODEL_PATH: Path = Path("detection/models/efficientnet_v2.pt")
    CLASSIFICATION_ENABLED: bool = True
    MODEL_DEVICE: str = "cpu"  # "cpu" | "cuda"
    IMAGE_SIZE: int = 640

    # ==================== DETECTION ====================
    DETECTION_CONFIDENCE_THRESHOLD: float = 0.25
    DETECTION_IOU_THRESHOLD: float = 0.45
    DETECTION_MAX_DETECTIONS: int = 10

    # ==================== CLASSIFICATION ====================
    CLASSIFICATION_NUM_CLASSES: int = 3
    WOUND_TYPES: list[str] = ["burn", "abrasion", "bruise"]
    SEVERITY_CLASSES: list[str] = ["mild", "moderate", "severe"]

    # ==================== UPLOAD ====================
    MAX_UPLOAD_SIZE: int = 5242880  # 5MB
    ALLOWED_EXTENSIONS: list[str] = [".jpg", ".jpeg", ".png"]
    MIN_IMAGE_WIDTH: int = 224
    MIN_IMAGE_HEIGHT: int = 224
    MAX_IMAGE_WIDTH: int = 4096
    MAX_IMAGE_HEIGHT: int = 4096

    # ==================== STORAGE ====================
    TEMP_UPLOAD_DIR: Path = Path("ai_ml/detection/temp")
    OUTPUT_DIR: Path = Path("ai_ml/detection/output")

    # ==================== BATCH ====================
    BATCH_SIZE: int = 8
    BATCH_WORKERS: str | int = "auto"
    BATCH_INPUT_DIR: Path = Path("ai_ml/detection/data/test/images")
    BATCH_OUTPUT_DIR: Path = Path("ai_ml/detection/output/batch_results")

    # ==================== SECURITY ====================
    API_KEY_ENABLED: bool = False
    API_KEY: Optional[str] = None

    # ==================== CORS ====================
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ==================== VALIDATORS ====================
    @field_validator("WOUND_TYPES", "SEVERITY_CLASSES", "ALLOWED_EXTENSIONS", "CORS_ORIGINS", mode="before")
    @classmethod
    def parse_csv_list(cls, v) -> list[str]:
        if isinstance(v, str):
            try:
                import json
                if v.startswith('[') and v.endswith(']'):
                    return json.loads(v)
            except:
                pass
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @field_validator("DETECTION_MODEL_PATH", "CLASSIFICATION_MODEL_PATH",
                     "TEMP_UPLOAD_DIR", "OUTPUT_DIR", "BATCH_INPUT_DIR",
                     "BATCH_OUTPUT_DIR", mode="before")
    @classmethod
    def parse_path(cls, v) -> Path:
        if isinstance(v, str):
            return Path(v).resolve()
        return Path(v) if v else Path(".").resolve()

    @field_validator("BATCH_WORKERS", mode="before")
    @classmethod
    def parse_batch_workers(cls, v) -> int:
        if isinstance(v, str) and v.lower() == "auto":
            return os.cpu_count() or 1
        return int(v)

    # ==================== POST INIT ====================
    def model_post_init(self, __context):
        # Create required directories
        for directory in [self.TEMP_UPLOAD_DIR, self.OUTPUT_DIR, self.BATCH_OUTPUT_DIR]:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logging.debug(f"✓ Directory created/exists: {directory}")
            except Exception as e:
                logging.error(f"Failed to create directory {directory}: {e}")

        if not self.DETECTION_MODEL_PATH.exists():
            msg = f"Detection model not found: {self.DETECTION_MODEL_PATH}"
            if self.is_production:
                raise FileNotFoundError(msg)
            logging.warning("" + msg)

        if self.CLASSIFICATION_ENABLED and not self.CLASSIFICATION_MODEL_PATH.exists():
            msg = f"Classification model not found: {self.CLASSIFICATION_MODEL_PATH}"
            if self.is_production:
                raise FileNotFoundError(msg)
            logging.warning("" + msg)

    # ==================== HELPERS ====================
    @property
    def is_production(self) -> bool:
        return self.APP_ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENVIRONMENT.lower() == "development"


# ==================== INIT SETTINGS ====================
settings = Settings()

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logging.info(f"{settings.APP_NAME} v{settings.APP_VERSION}")
logging.info(f"Environment: {settings.APP_ENVIRONMENT}")
logging.info(f"Working directory: {Path.cwd()}")
logging.info(f"Model device: {settings.MODEL_DEVICE}")
logging.info(f"Classification: {'Enabled' if settings.CLASSIFICATION_ENABLED else 'Disabled'}")