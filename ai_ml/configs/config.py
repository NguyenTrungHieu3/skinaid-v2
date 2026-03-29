from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class AISettings(BaseSettings):
    # ================== Service Info ==================
    APP_NAME: str = "Wound Detection & Classification API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    AI_MODEL_VERSION: str = "YOLOv11 and EfficientnetB3"

    # ================== YOLO Detection Model ==================
    YOLO_MODEL_NAME: str = "yolov11"
    YOLO_MODEL_PATH: str = "models/detection/weights/best_v2.pt"
    YOLO_CONF_THRESHOLD: float = 0.55
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
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

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
