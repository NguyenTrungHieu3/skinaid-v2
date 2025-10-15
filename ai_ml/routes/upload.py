"""
Upload route - Backend integration endpoint
Endpoint: POST /detect_and_classify
"""
from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path
import os, sys, time
import numpy as np
import cv2

router = APIRouter(tags=["Backend Integration"])

load_dotenv()
AI_API_KEY = os.getenv("AI_API_KEY")

ai_ml_root = Path(__file__).parent.parent
sys.path.insert(0, str(ai_ml_root))

from pipeline.analyzer import WoundAnalyzer

analyzer = WoundAnalyzer(
    yolo_model_path=str(ai_ml_root / "models/detection/weights/model_2_class_v1.pt"),
    efficientnet_model_path=str(ai_ml_root / "models/classification/weights/final_model.pth")
)

@router.post("/detect_and_classify")
async def detect_and_classify(
    file: UploadFile = File(...), 
    x_api_key: str = Header(None, alias="X-API-Key")
) -> Dict[str, Any]:
    """
    Backend integration endpoint
    - Accepts image file
    - Requires X-API-Key header
    - Returns detection + classification results
    """
    if not x_api_key or x_api_key != AI_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

    try:
        start_time = time.time()
        contents = await file.read()
        np_array = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if img is None:
            return {
                "success": False,
                "error": "Cannot read image",
                "error_code": "INVALID_IMAGE",
                "num_detections": 0,
                "detections": []
            }

        results = analyzer.analyze(img)
        
        return {
            "success": True,
            "num_detections": len(results) if results else 0,
            "detections": results if results else [],
            "processing_time": round(time.time() - start_time, 3),
            "ai_model_version": "yolo_v11 + efficientnet_b0"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_code": "PROCESSING_ERROR",
            "num_detections": 0,
            "detections": []
        }
