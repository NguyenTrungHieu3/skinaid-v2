from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UUID
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from app.modules.ai.models.wound_analysis import WoundAnalysis


class WoundDetection(SQLModel, table=True):
    __tablename__ = "wound_detections"

    detection_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )
    analysis_id: uuid.UUID = Field(
        foreign_key="wound_analyses.analysis_id",
        index=True
    )

    wound_type: str = Field(max_length=100)
    severity: str = Field(max_length=100)
    sub_type: Optional[str] = Field(max_length=100, default=None)
    confidence_score: float = Field(ge=0.0, le=1.0)

    bounding_box: dict = Field(sa_column=Column(JSONB, nullable=False))

    detection_index: int = Field(default=0, ge=0)

    firstaidguide_id: Optional[uuid.UUID] = Field(
        default=None,
        nullable=True,
        foreign_key="firstaid_guides.firstaidguide_id"
    )

    firstaid_snapshot: dict = Field(sa_column=Column(JSONB, nullable=True))

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    wound_analysis: Optional["WoundAnalysis"] = Relationship(
        back_populates="wound_detections"
    )

    @classmethod
    def create_detection(
        cls,
        analysis_id: uuid.UUID,
        wound_type: str,
        severity: str,
        sub_type: Optional[str] = None,
        confidence_score: float = 0.0,
        bounding_box: dict = None,
        detection_index: int = 0,
        firstaidguide_id: Optional[uuid.UUID] = None,
        firstaid_snapshot: dict = None
    ) -> "WoundDetection":
        return cls(
            analysis_id=analysis_id,
            wound_type=wound_type,
            severity=severity,
            sub_type=sub_type,
            confidence_score=confidence_score,
            bounding_box=bounding_box or {},
            detection_index=detection_index,
            firstaidguide_id=firstaidguide_id,
            firstaid_snapshot=firstaid_snapshot,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )