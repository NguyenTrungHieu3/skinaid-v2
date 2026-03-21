from uuid import uuid4, UUID
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator

from app.modules.firstaid.schemas.domain import FirstAidGuideBase


class GuideSource(BaseModel):
    """Source information for first aid guide."""
    name: str
    url: Optional[str] = None


class GuideContentMixin(BaseModel):
    steps: List[str] = Field(default_factory=list)
    dos: List[str] = Field(default_factory=list)
    donts: List[str] = Field(default_factory=list)
    supplies_needed: List[str] = Field(default_factory=list)
    source: Optional[Any] = Field(default=None, validate_default=True)

    @field_validator("steps", "dos", "donts", "supplies_needed", mode="before")
    @classmethod
    def flatten_jsonb_list(cls, v):
        if v is None:
            return []
        if isinstance(v, dict):
            return v.get("items", [])
        if isinstance(v, list):
            return v
        return []

    @field_validator("source", mode="before")
    @classmethod
    def flatten_jsonb_source(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):
            # Check if it's wrapped {"source": {...}} or direct {name, url}
            if "source" in v:
                inner = v.get("source")
                if isinstance(inner, dict):
                    return GuideSource.model_validate(inner)
                return inner
            # Direct format {name, url}
            return GuideSource.model_validate(v)
        elif isinstance(v, str):
            # Legacy format: just source name as string
            return GuideSource(name=v, url=None)
        return v


class FirstAidGuideResponse(FirstAidGuideBase, GuideContentMixin):
    firstaidguide_id: UUID
    version: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    @field_validator("created_by", mode="before")
    @classmethod
    def convert_created_by(cls, v):
        if v is None:
            return None
        if isinstance(v, UUID):
            return str(v)
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


class CreateGuideRequest(FirstAidGuideBase, GuideContentMixin):
    pass


class UpdateGuideRequest(BaseModel):
    title: Optional[str] = None
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
