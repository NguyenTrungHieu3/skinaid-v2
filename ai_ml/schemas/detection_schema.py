from pydantic import BaseModel
from typing import List

class DetectionBox(BaseModel):
    class_name: str
    confidence: float
    bbox: List[float]

class YOLODetectionResponse(BaseModel):
    success: bool = True
    predictor_name: str = "YOLOv11"
    detections: List[DetectionBox] = []
