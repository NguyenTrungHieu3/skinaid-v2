from typing import Optional, List

from pydantic import BaseModel, Field, model_validator


class GuideItem(BaseModel):
    items: List[str] = Field(default_factory=list)

# Wound types that don't require severity
NO_SEVERITY_TYPES = {"psoriasis", "fungal"}


class FirstAidGuideBase(BaseModel):
    wound_type: str = Field(...,
                            description="Loại vết thương (abrasion, cut, burn, etc.)")
    severity: Optional[str] = Field(None, description="Mức độ (mild, moderate, severe). Không bắt buộc cho psoriasis, fungal.")
    sub_type: Optional[str] = Field(
        None, description="Loại phụ (ví dụ: blister cho burn)")
    title: str = Field(..., description="Tiêu đề hướng dẫn")

    estimated_healing_time: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False

    @model_validator(mode="after")
    def set_default_severity(self):
        """Auto-set severity to 'general' for wound types that don't need it."""
        if self.wound_type and self.wound_type.lower() in NO_SEVERITY_TYPES:
            if not self.severity:
                self.severity = "general"
        elif not self.severity:
            self.severity = "mild"  # fallback default
        return self

