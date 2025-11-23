from sqlmodel import SQLModel, Field, Relationship, Column, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UUID
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from app.modules.ai.models.wound_detection import WoundDetection


class WoundAnalysis(SQLModel, table=True):
    __tablename__ = "wound_analyses"

    __table_args__ = (
        CheckConstraint(
            '(user_id IS NOT NULL AND session_id IS NULL) OR '
            '(user_id IS NULL AND session_id IS NOT NULL)',
            name='chk_wound_analyses_identifier'
        ),
    )

    analysis_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="users.user_id",
        index=True,
        nullable=True
    )
    session_id : Optional[uuid.UUID] = Field(
        default=None, 
        foreign_key="guest_sessions.session_id",
        index=True,
        nullable=True
    )

    image_url: str = Field(max_length=500)
    file_name: str = Field(max_length=255)
    file_size: int = Field(gt=0)

    ai_model_version: str = Field(max_length=100, default="YOLOv11_EfficientNetV2_1.0")
    total_detections: int = Field(default=0, ge=0)
    processing_time_ms: int = Field(gt=0)

    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted: bool = Field(default=False)

    wound_detections: List["WoundDetection"] = Relationship(
        back_populates="wound_analysis",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @property
    def is_guest_analysis(self)->bool:
        return self.user_id is None and self.session_id is not None

    @property
    def average_confidence(self) -> float:
        if not hasattr(self, 'wound_detections') or not self.wound_detections:
            return 0.0
        try:
            total = sum(d.confidence_score for d in self.wound_detections)
            return total / len(self.wound_detections)
        except (AttributeError, ZeroDivisionError):
            return 0.0

    @classmethod
    def create_analysis(
        cls,
        image_url: str,
        file_name: str,
        file_size: int,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[uuid.UUID] = None,
        ai_model_version: str = "YOLOv11_EfficientNetV2_1.0",
        total_detections: int = 0,
        processing_time_ms: int = 0,
        analyzed_at: Optional[datetime] = None
    ) -> "WoundAnalysis":
        
        if user_id is None and session_id is None:
            raise ValueError("Phải cung cấp user_id hoặc session_id để phân tích vết thương") 
        
        if user_id is not None and session_id is not None:
            raise ValueError(
                "Không thể cung cấp cả user_id và session_id."
                "Sử dụng user_id cho người dùng được xác thực, session_id cho khách."
            )

        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        return cls(
            user_id=user_id,
            session_id=session_id,
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

    def __repr__(self) -> str:
        identifier = f"user={self.user_id}" if self.user_id else f"session={self.session_id}"
        return f"<WoundAnalysis({identifier}, detections={self.total_detections})>"