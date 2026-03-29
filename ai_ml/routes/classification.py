from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from typing import Any
from dotenv import load_dotenv
from pathlib import Path
import os, sys
import numpy as np
import cv2

router = APIRouter(prefix="/classify", tags=["EfficientNet Classification"])

load_dotenv()
AI_API_KEY = os.getenv("AI_API_KEY")

ai_ml_root = Path(__file__).parent.parent
sys.path.insert(0, str(ai_ml_root))

from models.classification.wound_classifier import SeverityClassifier
from schemas.classification_schema import ClassificationResult, EfficientNetResponse

classifier = SeverityClassifier(str(ai_ml_root / "models/classification/weights/final_model_v2.pth"))

@router.post("/", response_model=EfficientNetResponse)
async def classify_wound(
    file: UploadFile = File(...),
    x_api_key: str = Header(None, alias="X-API-Key")
) -> Any:
    if AI_API_KEY and (not x_api_key or x_api_key != AI_API_KEY):
        raise HTTPException(status_code=403, detail="Invalid API key")

    try:
        contents = await file.read()
        np_array = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        severity, confidence = classifier.classify(img)

        classification_result = ClassificationResult(
            severity=severity,
            severity_confidence=confidence
        )

        return EfficientNetResponse(
            success=True,
            classifier_name="EfficientnetB0",
            classifications=[classification_result]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")
