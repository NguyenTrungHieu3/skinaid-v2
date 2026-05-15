from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union


class AISettings(BaseSettings):
    # ================== Service Info ==================
    APP_NAME: str = "Wound Detection & Classification API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    AI_MODEL_VERSION: str = "YOLOv11 and EfficientnetB3"

    # ================== Server ==================
    # Dùng 0.0.0.0 để Docker container có thể nhận request từ bên ngoài
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    WORKERS: int = 1
    RELOAD: bool = False

    # ================== YOLO Detection Model ==================
    YOLO_MODEL_NAME: str = "yolov11"
    YOLO_MODEL_PATH: str = "models/detection/weights/best_v2.pt"
    YOLO_CONF_THRESHOLD: float = 0.25
    YOLO_IMG_SIZE: int = 640

    # ================== EfficientNet Classification Model ==================
    EFFICIENTNET_MODEL_NAME: str = "efficientnet_b3"
    EFFICIENTNET_MODEL_PATH: str = "models/classification/weights/final_model_v2.pth"
    EFFICIENTNET_NUM_CLASSES: int = 12
    EFFICIENTNET_PRETRAINED: bool = False
    EFFICIENTNET_DEVICE: str = "cpu"

    # ================== Image Processing ==================
    IMAGE_SIZE: int = 224
    IMAGE_MEAN: List[float] = [0.485, 0.456, 0.406]
    IMAGE_STD: List[float] = [0.229, 0.224, 0.225]

    # ================== Classification Classes ==================
    WOUND_CLASSES: List[str] = [
        "abrasion_mild",
        "abrasion_moderate",
        "acne_mild",
        "acne_moderate",
        "acne_severe",
        "bruise_mild",
        "bruise_moderate",
        "burn_mild",
        "burn_moderate_blister",
        "burn_moderate_skintear",
        "psoriasis",
        "ringworm"
    ]
    
    # ================== CORS Configuration ==================
    # Đọc từ env: AI_CORS_ORIGINS=http://backend:8000,http://localhost:8000
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse comma-separated string or return list as-is."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ================== Rate Limiting Configuration ==================
    RATE_LIMIT: str = "100/day"
    
    # ================== Pydantic Settings Configuration ==================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AI_",
        case_sensitive=False,
        extra="ignore"
    )

# ================== Singleton Instance ==================
settings = AISettings()
