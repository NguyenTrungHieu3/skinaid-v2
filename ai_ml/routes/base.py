from fastapi import APIRouter
import time

router = APIRouter()

@router.get("/")
async def root():
    return {
        "service": "Wound Detection & Classification API",
        "version": "1.0.0",
        "status": "running"
    }

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AI",
        "timestamp": time.time()
    }

@router.get("/model-info")
async def get_model_info():
    return {
        "detection_model": "YOLO v11",
        "classification_model": "EfficientNet B0",
        "num_wound_classes": 7,
        "wound_classes": [
            "abrasion mild",
            "abrasion moderate", 
            "bruise mild",
            "bruise moderate",
            "burn mild",
            "burn moderate blister",
            "burn moderate skintear"
        ]
    }
