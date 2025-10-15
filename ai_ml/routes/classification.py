from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from typing import Any
from dotenv import load_dotenv
from pathlib import Path
import os, sys, time
import numpy as np
import cv2

router = APIRouter(prefix="/classify", tags=["EfficientNet Classification"])

# Load API key
load_dotenv()
AI_API_KEY = os.getenv("AI_API_KEY")

# Add project root
ai_ml_root = Path(__file__).parent.parent
sys.path.insert(0, str(ai_ml_root))

# Import models & schemas
from models.classification.wound_classifier import SeverityClassifier
from schemas.classification_schema import ClassificationResult, EfficientNetResponse

# Load model
classifier = SeverityClassifier(str(ai_ml_root / "models/classification/weights/final_model.pth"))

@router.post("/", response_model=EfficientNetResponse)
async def classify_wound(
    file: UploadFile = File(...),
    x_api_key: str = Header(None, alias="X-API-Key")
) -> Any:
    """API chỉ trả về kết quả classification theo đúng schema EfficientNetResponse"""
    if not x_api_key or x_api_key != AI_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

    try:
        contents = await file.read()
        np_array = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Phân loại mức độ
        severity, confidence = classifier.classify(img)

        # Chuyển sang schema Pydantic
        classification_result = ClassificationResult(
            severity=severity,
            severity_confidence=confidence
        )

        # Trả về đúng cấu trúc EfficientNetResponse
        return EfficientNetResponse(
            classifications=[classification_result]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
