from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class WoundAnalysisBase(BaseModel):
    user_id: Optional[str] = None
    
    image_url: str
    file_name: str
    file_size: int
    ai_model_version: str = "YOLOv11_EfficientNetV2_1.0"
    total_detections: int = 0
    processing_time_ms: int
    primary_wound_type: str = "not_wound"
    primary_severity: str = "mild"
    primary_firstaidguide_id: Optional[str] = None
    firstaid_snapshot: Dict[str, Any]
    analyzed_at: Optional[datetime] = None


class WoundAnalysisUpdate(BaseModel):
    total_detections: Optional[int] = None
    processing_time_ms: Optional[int] = None
    primary_wound_type: Optional[str] = None
    primary_severity: Optional[str] = None
    primary_firstaidguide_id: Optional[str] = None
    firstaid_snapshot: Optional[Dict[str, Any]] = None


class WoundDetectionSummary(BaseModel):
    wound_type: str
    severity: str
    confidence_score: float
    bounding_box: Dict[str, Any]
    is_primary: bool


class WoundAnalysisResponse(WoundAnalysisBase):
    analysis_id: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    # Computed fields
    is_successful_analysis: bool
    has_multiple_wounds: bool
    is_wound_detected: bool
    processing_time_seconds: Optional[float] = None
    average_confidence: float
    meets_accuracy_threshold: bool
    
    is_guest_analysis: bool = False

    significant_wounds: List[WoundDetectionSummary] = []
    
    class Config:
        from_attributes = True