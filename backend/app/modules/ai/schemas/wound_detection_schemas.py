from pydantic import BaseModel, Field, computed_field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class WoundDetectionBase(BaseModel):
    analysis_id: uuid.UUID
    wound_type: str
    severity: str
    sub_type: Optional[str] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    bounding_box: Dict[str, Any]
    detection_index: int = 0
    firstaidguide_id: Optional[uuid.UUID] = None
    firstaid_snapshot: Optional[Dict[str, Any]] = None

class WoundDetectionResponse(WoundDetectionBase):
    detection_id: uuid.UUID
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
        return severity_map.get(self.severity.lower() if self.severity else "", "Không xác định")

    class Config:
        from_attributes = True
