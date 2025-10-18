from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class WoundDetectionBase(BaseModel):
    analysis_id: str
    wound_type: str  # loại vết thương từ YOLOv11
    severity: str    # mức độ từ EfficientNetV2
    confidence_score: float  # độ tin cậy ≥ 0.65
    bounding_box: Dict[str, Any]  # tọa độ từ YOLOv11
    detection_index: int = 0  
    is_primary: bool = False   
    firstaidguide_id: str     


class WoundDetectionCreate(WoundDetectionBase):
    pass


class WoundDetectionUpdate(BaseModel):
    wound_type: Optional[str] = None
    severity: Optional[str] = None
    confidence_score: Optional[float] = None
    bounding_box: Optional[Dict[str, Any]] = None
    is_primary: Optional[bool] = None
    firstaidguide_id: Optional[str] = None


class WoundDetectionResponse(WoundDetectionBase):
    detection_id: str
    created_at: datetime

    confidence_percentage: float
    bounding_box_area: Optional[float] = None
    severity_display: str
    is_high_confidence: bool
    is_reliable: bool 
    meets_accuracy_threshold: bool  