from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UUID
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from app.modules.ai.models.wound_detection import WoundDetection


class WoundAnalysis(SQLModel, table=True):
    __tablename__ = "wound_analyses"

    analysis_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )
    user_id: Optional[uuid.UUID] = Field(
        foreign_key="users.user_id",
        index=True
    )

    image_url: str = Field(max_length=500)
    file_name: str = Field(max_length=255)
    file_size: int = Field(gt=0)

    ai_model_version: str = Field(max_length=100, default="YOLOv11_EfficientNetV2_1.0")
    total_detections: int = Field(default=0, ge=0)
    processing_time_ms: int = Field(gt=0)

    # Removed primary fields and firstaid_snapshot as per schema update

    analyzed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    is_deleted: bool = Field(default=False)

    wound_detections: List["WoundDetection"] = Relationship(
        back_populates="wound_analysis",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @property
    def average_confidence(self) -> float:
        if 'wound_detections' not in self.__dict__:
            return 0.0
        
        if not self.wound_detections:
            return 0.0

        try:
            total = sum(d.confidence_score for d in self.wound_detections)
            return total / len(self.wound_detections)
        except (AttributeError, ZeroDivisionError):
            return 0.0

    @classmethod
    def create_analysis(
        cls,
        user_id: Optional[uuid.UUID],
        image_url: str,
        file_name: str,
        file_size: int,
        ai_model_version: str = "YOLOv11_EfficientNetV2_1.0",
        total_detections: int = 0,
        processing_time_ms: int = 0,
        analyzed_at: Optional[datetime] = None
    ) -> "WoundAnalysis":
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        return cls(
            user_id=user_id,
            image_url=image_url,
            file_name=file_name,
            file_size=file_size,
            ai_model_version=ai_model_version,
            total_detections=total_detections,
            processing_time_ms=processing_time_ms,
            analyzed_at=analyzed_at or current_time,
            created_at=current_time,
            updated_at=current_time,
            is_deleted=False
        )

    def mark_as_deleted(self) -> None:
        self.is_deleted = True
        self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)