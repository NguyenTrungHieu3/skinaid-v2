from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UUID, Column, ForeignKey
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from app.modules.ai.models.analysis import Analysis


class Detection(SQLModel, table=True):
    __tablename__ = "detections"

    detection_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    analysis_id: uuid.UUID = Field(foreign_key="analyses.analysis_id", index=True)
    classification_result_id: Optional[uuid.UUID] = Field(default=None, foreign_key="ai_results.result_id")

    detection_index: int = Field(default=0, ge=0)
    bounding_box: dict = Field(sa_column=Column(JSONB, nullable=False))
    confidence: float = Field(ge=0.0, le=1.0)
    
    detected_class: str = Field(max_length=50)
    
    wound_type: Optional[str] = Field(default=None, max_length=50)
    severity: Optional[str] = Field(default=None, max_length=50)
    sub_type: Optional[str] = Field(default=None, max_length=50)
    detail_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    firstaidguide_id: Optional[uuid.UUID] = Field(default=None, foreign_key="firstaid_guides.firstaidguide_id")
    firstaid_snapshot: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    firstaid_snapshot_version: Optional[int] = Field(default=None)
    
    is_validated: bool = Field(default=False)
    validated_by: Optional[uuid.UUID] = Field(default=None, foreign_key="users.user_id")
    validated_at: Optional[datetime] = Field(default=None)
    validation_notes: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    wound_analysis: Optional["Analysis"] = Relationship(
        back_populates="wound_detections"
    )