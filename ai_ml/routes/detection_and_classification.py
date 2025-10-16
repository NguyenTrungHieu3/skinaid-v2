from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path
import os, sys, time
import numpy as np
import cv2

from schemas.detection_and_classification_schema import CombinedResponse, WoundDetectionAndClassification 

router = APIRouter(prefix="/analyze", tags=["YOLO + EfficientNet"])

load_dotenv()
AI_API_KEY = os.getenv("AI_API_KEY")

ai_ml_root = Path(__file__).parent.parent
sys.path.insert(0, str(ai_ml_root))

from pipeline.analyzer import WoundAnalyzer
analyzer = WoundAnalyzer(
    yolo_model_path=str(ai_ml_root / "models/detection/weights/model_2_class_v1.pt"),
    efficientnet_model_path=str(ai_ml_root / "models/classification/weights/final_model.pth")
)

@router.post("/", response_model=CombinedResponse)
async def analyze_wound(
    file: UploadFile = File(...),
    x_api_key: str = Header(None, alias="X-API-Key")
) -> CombinedResponse:
    if not x_api_key or x_api_key != AI_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

    try:
        contents = await file.read()
        np_array = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image")

        results_raw = analyzer.analyze(img)

        detections = []
        for det in results_raw:
            severity_label = det.get("severity", "")
            parts = severity_label.split(" ", 1)
            class_name = parts[0] if len(parts) > 0 else det.get("class_name", "")
            severity = parts[1] if len(parts) > 1 else "unknown"

            detection = WoundDetectionAndClassification(
                class_name=class_name,
                confidence=det.get("wound_confidence", det.get("confidence", 0.0)),
                bbox=det.get("bbox", []),
                severity=severity,
                severity_confidence=det.get("severity_confidence", 0.0)
            )
            detections.append(detection)

        response = CombinedResponse(
            success=True,
            num_detections=len(detections),
            detections=detections,
            ai_model_version="YOLO + EfficientNet"
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
