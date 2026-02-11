import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator

from app.modules.firstaid.schemas.domain import FirstAidGuideBase


# ── Shared Mixins ────────────────────────────────────────────────────────────


class GuideContentMixin(BaseModel):
    steps: List[str] = Field(default_factory=list)
    dos: List[str] = Field(default_factory=list)
    donts: List[str] = Field(default_factory=list)
    supplies_needed: List[str] = Field(default_factory=list)
    source: Optional[str] = None


# ── Response Models ──────────────────────────────────────────────────────────


class FirstAidGuideResponse(FirstAidGuideBase, GuideContentMixin):
    firstaidguide_id: uuid.UUID
    version: int
    created_by: Optional[str] = None  # Return ID as string
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    @field_validator("steps", "dos", "donts", "supplies_needed", mode="before")
    @classmethod
    def flatten_jsonb_list(cls, v):
        """Convert {'items': [...]} to [...] if needed."""
        if isinstance(v, dict):
            return v.get("items", [])
        return v

    @field_validator("source", mode="before")
    @classmethod
    def flatten_jsonb_source(cls, v):
        """Convert {'source': '...'} to '...' if needed."""
        if isinstance(v, dict):
            return v.get("source")
        return v

    class Config:
        from_attributes = True


class GuideStatsResponse(BaseModel):
    total_guides: int
    active_guides: int
    wound_type_breakdown: Dict[str, int]
    severity_breakdown: Dict[str, int]
    coverage_percentage: float


class GuideValidationResponse(BaseModel):
    is_complete: bool
    issues: List[str]
    completeness_score: int


# ── Request Models ───────────────────────────────────────────────────────────


class CreateGuideRequest(FirstAidGuideBase, GuideContentMixin):
    pass


class UpdateGuideRequest(BaseModel):
    title: Optional[str] = None
    # Usually not updated, but API might allow
    wound_type: Optional[str] = None
    severity: Optional[str] = None
    sub_type: Optional[str] = None

    steps: Optional[List[str]] = None
    dos: Optional[List[str]] = None
    donts: Optional[List[str]] = None
    supplies_needed: Optional[List[str]] = None
    source: Optional[str] = None

    estimated_healing_time: Optional[str] = None
    is_active: Optional[bool] = None
