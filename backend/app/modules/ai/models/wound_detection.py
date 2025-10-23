from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from app.modules.ai.models.wound_analysis import WoundAnalysis


class WoundDetection(SQLModel, table=True):
    __tablename__ = "wound_detections"

    detection_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), 
        primary_key=True
    )
    analysis_id: str = Field(
        foreign_key="wound_analyses.analysis_id", 
        index=True
    )

    wound_type: str = Field(max_length=100)
    severity: str = Field(max_length=50)
    confidence_score: float = Field(ge=0.0, le=1.0)

    bounding_box: dict = Field(sa_column=Column(JSONB, nullable=False))

    detection_index: int = Field(default=0, ge=0)
    is_primary: bool = Field(default=False)
    
    firstaidguide_id: Optional[str] = Field(
        default=None,
        nullable=True,
        foreign_key="firstaid_guides.firstaidguide_id"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    wound_analysis: Optional["WoundAnalysis"] = Relationship(
        back_populates="wound_detections"
    )

    @classmethod
    def create_detection(
        cls,
        analysis_id: str,
        wound_type: str,
        severity: str,
        confidence_score: float,
        bounding_box: dict,
        detection_index: int = 0,
        is_primary: bool = False,
        firstaidguide_id: Optional[str] = None
    ) -> "WoundDetection":
        return cls(
            analysis_id=analysis_id,
            wound_type=wound_type,
            severity=severity,
            confidence_score=confidence_score,
            bounding_box=bounding_box,
            detection_index=detection_index,
            is_primary=is_primary,
            firstaidguide_id=firstaidguide_id,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )