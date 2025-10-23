from pydantic import BaseModel, Field, computed_field
from typing import Optional, Dict, Any
from datetime import datetime


class WoundDetectionBase(BaseModel):
    analysis_id: str
    wound_type: str
    severity: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    bounding_box: Dict[str, Any]
    detection_index: int = 0
    is_primary: bool = False
    firstaidguide_id: Optional[str] = None


class WoundDetectionCreate(WoundDetectionBase):
    pass
class WoundDetectionResponse(WoundDetectionBase):
    detection_id: str
    created_at: datetime

    @computed_field
    @property
    def confidence_percentage(self) -> float:
        return round(self.confidence_score * 100, 2)

    @computed_field
    @property
    def meets_accuracy_threshold(self) -> bool:
        return self.confidence_score >= 0.65

    @computed_field
    @property
    def bounding_box_area(self) -> Optional[float]:
        if not self.bounding_box:
            return None
        
        try:
            width = self.bounding_box.get("width", 0)
            height = self.bounding_box.get("height", 0)
            return width * height
        except (KeyError, TypeError):
            return None

    @computed_field
    @property
    def severity_display(self) -> str:
        """Get severity in Vietnamese."""
        severity_map = {
            "mild": "Nhẹ",
            "moderate": "Trung bình",
            "severe": "Nặng"
        }
        return severity_map.get(
            self.severity.lower() if self.severity else "", 
            "Không xác định"
        )

    class Config:
        from_attributes = True

class WoundDetectionSummary(BaseModel):
    wound_type: str
    severity: str
    confidence_score: float
    bounding_box: Dict[str, Any]
    is_primary: bool
    
    @computed_field
    @property
    def confidence_percentage(self) -> float:
        return round(self.confidence_score * 100, 2)
    
    @computed_field
    @property
    def meets_threshold(self) -> bool:
        return self.confidence_score >= 0.65