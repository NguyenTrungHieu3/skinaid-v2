from pydantic import BaseModel
from typing import List, Dict

class WoundDetectionAndClassification(BaseModel):
    wound_type: str
    severity: str
    confidence_score: float
    bbox: Dict

class CombinedResponse(BaseModel):
    success: bool = True
    ai_model_version: str
    total_detections: int
    processing_time_ms: int 
    primary_wound_type: str
    detections: List[WoundDetectionAndClassification]
