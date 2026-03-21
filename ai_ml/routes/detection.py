from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path
import os, sys
import numpy as np
import cv2

router = APIRouter(prefix="/detect", tags=["YOLO Detection"])

load_dotenv()
AI_API_KEY = os.getenv("AI_API_KEY")

ai_ml_root = Path(__file__).parent.parent
sys.path.insert(0, str(ai_ml_root))

from models.detection.wound_detector import WoundDetector
from schemas.detection_schema import DetectionBox, YOLODetectionResponse

detector = WoundDetector(str(ai_ml_root / "models/detection/weights/best_v2.pt"))

@router.post("/", response_model=YOLODetectionResponse)
async def detect_wound(file: UploadFile = File(...), x_api_key: str = Header(None, alias="X-API-Key")):
    if AI_API_KEY and (not x_api_key or x_api_key != AI_API_KEY):
        raise HTTPException(status_code=403, detail="Invalid API key")

    try:
        contents = await file.read()
        np_array = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image")

        detections_raw = detector.detect(img)
        detections = [DetectionBox(**det) for det in detections_raw]

        return YOLODetectionResponse(
            success=True,
            predictor_name="YOLO v11",
            detections=detections
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection error: {str(e)}")
