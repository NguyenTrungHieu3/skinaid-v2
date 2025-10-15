from pydantic import BaseModel
from typing import List

class DetectionBox(BaseModel):
    class_name: str
    confidence: float
    bbox: List[float]

class YOLODetectionResponse(BaseModel):
    predictor_name: str = "YOLO"
    detections: List[DetectionBox] = []
