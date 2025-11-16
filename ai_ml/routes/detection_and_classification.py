from fastapi import APIRouter, UploadFile, File, Header, HTTPException, Request
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path
import os, sys, time
import numpy as np
import cv2

from middleware.rate_limiter import limiter
from schemas.detection_and_classification_schema import CombinedResponse, WoundDetectionAndClassification 
from configs.config import settings

router = APIRouter(prefix="/analyze", tags=["Detect and Classify"])

load_dotenv()
AI_API_KEY = os.getenv("AI_API_KEY")

ai_ml_root = Path(__file__).parent.parent
sys.path.insert(0, str(ai_ml_root))

from pipeline.analyzer import WoundAnalyzer
analyzer = WoundAnalyzer(
    yolo_model_path=str(ai_ml_root / settings.YOLO_MODEL_PATH),
    efficientnet_model_path=str(ai_ml_root / settings.EFFICIENTNET_MODEL_PATH)
)

@router.post("/", response_model=CombinedResponse)
@limiter.limit(settings.RATE_LIMIT)
async def analyze_wound(
    request: Request,
    file: UploadFile = File(...),
    x_api_key: str = Header(None, alias="X-API-Key")
) -> CombinedResponse:
    start_time = time.time()
    
    if not x_api_key or x_api_key != AI_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

    try:
        # Read and decode image
        contents = await file.read()
        np_array = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Analyze image
        results_raw = analyzer.analyze(img)

        # --- SỬA LỖI TẠI ĐÂY ---
        # 1. Xử lý rõ ràng trường hợp 'None' (Lỗi 'NoneType' object is not iterable)
        if results_raw is None:
            # Nếu AI trả về None, coi nó như danh sách rỗng
            results_raw = []
        
        if not results_raw:
            # No detections found
            processing_time = time.time() - start_time
            return CombinedResponse(
                success=True,
                ai_model_version=settings.AI_MODEL_VERSION,
                total_detections=0,
                processing_time_ms=int(processing_time * 1000),
                primary_wound_type="none",
                detections=[] # <-- Luôn trả về danh sách rỗng
            )

        # Process detections
        detections = []
        primary_wound = results_raw[0].get("class_name", "wound") if results_raw else "none"
        
        # Check if primary wound is "normal skin"
        processing_time = time.time() - start_time
        if primary_wound.lower() == "normal skin":
            return CombinedResponse(
                success=True,
                ai_model_version=settings.AI_MODEL_VERSION,
                total_detections=0,
                processing_time_ms=int(processing_time * 1000),
                primary_wound_type="normal skin",
                # detections=None
                detections=[] # Sửa: Luôn trả về danh sách rỗng thay vì None
            )
        
        # (Đoạn code này giờ đã an toàn vì results_raw không thể là None)
        for det in results_raw:
            try:
                severity_label = det.get("severity", "") # burn_moderate
                parts = severity_label.split("_", 1) # parts = [burn, moderate]
                wound_type = parts[0] if len(parts) > 0 else det.get("class_name", "wound")
                severity = parts[1] if len(parts) > 1 else "unknown"

                detection = WoundDetectionAndClassification(
                    wound_type=wound_type,
                    severity=severity,
                    confidence_score=round(det.get("severity_confidence", 0.0), 2),
                    bbox={
                        "x": int(det["bbox"][0]),
                        "y": int(det["bbox"][1]),
                        "width": int(det["bbox"][2] - det["bbox"][0]),
                        "height": int(det["bbox"][3] - det["bbox"][1])
                    }
                )
                detections.append(detection)
            except Exception:
                # Skip invalid detection
                continue

        response = CombinedResponse(
            success=True,
            ai_model_version=settings.AI_MODEL_VERSION,
            total_detections=len(detections),
            processing_time_ms=int(processing_time * 1000),
            primary_wound_type=primary_wound,
            detections=detections
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
