from typing import Optional, List

from pydantic import BaseModel, Field


class GuideItem(BaseModel):
    items: List[str] = Field(default_factory=list)


class FirstAidGuideBase(BaseModel):
    wound_type: str = Field(...,
                            description="Loại vết thương (abrasion, cut, burn, etc.)")
    severity: str = Field(..., description="Mức độ (mild, moderate, severe)")
    sub_type: Optional[str] = Field(
        None, description="Loại phụ (ví dụ: blister cho burn)")
    title: str = Field(..., description="Tiêu đề hướng dẫn")

    estimated_healing_time: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False
