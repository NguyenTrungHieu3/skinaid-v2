from pydantic import BaseModel
from typing import List

class WoundDetectionAndClassification(BaseModel):
    class_name: str
    confidence: float
    bbox: List[float]
    severity: str
    severity_confidence: float

class CombinedResponse(BaseModel):
    success: bool = True
    num_detections: int
    detections: List[WoundDetectionAndClassification]
    ai_model_version: str = "YOLO + EfficientNet"
