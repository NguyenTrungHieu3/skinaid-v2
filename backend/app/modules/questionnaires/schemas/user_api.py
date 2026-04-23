from __future__ import annotations

from typing import List, Optional, Literal, Dict, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.questionnaires.schemas.api import QuestionResponse

SEVERITY_ORDER: Dict[str, int] = {"mild": 1, "moderate": 2, "severe": 3}
TRIAGE_ORDER: Dict[str, int] = {"green": 1, "yellow": 2, "red": 3}
ALLOWED_SEVERITIES = set(SEVERITY_ORDER.keys())
ALLOWED_TRIAGES = set(TRIAGE_ORDER.keys())

# User-side questionnaire view — skips admin wound_type allowlist so composite
# keys like "burn_blister" are accepted.
class QuestionnaireUserView(BaseModel):
    questionnaire_id: UUID
    wound_type: str
    title: str
    description: Optional[str] = None
    is_active: bool
    questions: List[QuestionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WoundDetectionInput(BaseModel):
    detection_id: Optional[UUID] = None
    wound_type: str = Field(..., min_length=1, max_length=64)
    subtype: Optional[str] = Field(default=None, max_length=64)
    severity: Optional[str] = Field(default=None)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @field_validator("wound_type")
    @classmethod
    def _norm_wound_type(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("subtype")
    @classmethod
    def _norm_subtype(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip().lower()
        return v or None

    @field_validator("severity")
    @classmethod
    def _norm_severity(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip().lower()
        if v not in ALLOWED_SEVERITIES:
            raise ValueError(
                f"severity phải thuộc {sorted(ALLOWED_SEVERITIES)}"
            )
        return v

class ResolveQuestionnairesRequest(BaseModel):
    detections: List[WoundDetectionInput] = Field(..., min_length=1)

class ResolvedQuestionnaireItem(BaseModel):
    wound_type: str
    subtype: Optional[str] = None
    severity: Optional[str] = None
    representative_detection_id: Optional[UUID] = None
    detection_count: int = Field(..., ge=1)
    questionnaire: QuestionnaireUserView

class MissingQuestionnaireItem(BaseModel):
    wound_type: str
    subtype: Optional[str] = None
    severity: Optional[str] = None
    detection_count: int = Field(..., ge=1)
    reason: str = "no_active_questionnaire"

class ResolveQuestionnairesResponse(BaseModel):
    questionnaires: List[ResolvedQuestionnaireItem] = Field(default_factory=list)
    missing: List[MissingQuestionnaireItem] = Field(default_factory=list)
    total_unique_keys: int = 0

class AnswerSelectionInput(BaseModel):
    question_id: UUID
    answer_ids: List[UUID] = Field(..., min_length=1)

class SubmitWoundResponseRequest(BaseModel):
    user_id: Optional[UUID] = None
    session_id: Optional[str] = Field(default=None, max_length=128)
    analysis_id: Optional[UUID] = None
    user_description: Optional[str] = Field(default=None, max_length=2000)

    detections: List[WoundDetectionInput] = Field(..., min_length=1)
    answers: List[AnswerSelectionInput] = Field(..., min_length=1)

    forward_to_synthesis: bool = Field(
        default=True,
        description="Nếu True → gọi LLM synthesize ngay sau khi validate",
    )

class AnswerSelectionView(BaseModel):
    question_id: UUID
    answer_ids: List[UUID]
    triage_levels: List[str] = Field(default_factory=list)

class SynthesisSummary(BaseModel):
    wound_type: str
    subtype: Optional[str] = None
    severity: str
    source: Literal["llm", "db"]
    guidance: str
    structured_guidance: Optional[Dict[str, Any]] = None
    validated: bool
    error: Optional[str] = None

class SubmitWoundResponseResponse(BaseModel):
    aggregated_triage: Literal["green", "yellow", "red"]
    selections: List[AnswerSelectionView]
    syntheses: List[SynthesisSummary] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
