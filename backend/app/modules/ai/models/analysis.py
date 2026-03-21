from sqlmodel import SQLModel, Field, Relationship, CheckConstraint
from sqlalchemy import UUID, Column, ForeignKey
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from app.modules.ai.models.detection import Detection


class Analysis(SQLModel, table=True):
    __tablename__ = "analyses"

    __table_args__ = (
        CheckConstraint(
            '(user_id IS NOT NULL AND guest_session_id IS NULL) OR '
            '(user_id IS NULL AND guest_session_id IS NOT NULL)',
            name='chk_wound_analyses_identifier'
        ),
    )

    analysis_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.user_id", index=True, nullable=True)
    guest_session_id: Optional[uuid.UUID] = Field(default=None, foreign_key="guest_sessions.session_id", index=True, nullable=True)

    image_url: str = Field(max_length=500)
    image_hash: Optional[str] = Field(default=None, max_length=64)
    image_size_bytes: Optional[int] = Field(default=None, gt=0)
    image_dimensions: Optional[str] = Field(default=None, max_length=20)

    status: str = Field(default="queued", max_length=20)
    status_reason: Optional[str] = Field(default=None, max_length=255)

    wound_type: Optional[str] = Field(default=None, max_length=50)
    severity: Optional[str] = Field(default=None, max_length=50)
    sub_type: Optional[str] = Field(default=None, max_length=50)
    confidence: Optional[float] = Field(default=None)

    model_id: Optional[uuid.UUID] = Field(default=None, foreign_key="ai_models.model_id", nullable=True)
    model_version: Optional[str] = Field(default=None, max_length=50)

    queued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    is_offline: bool = Field(default=False)
    offline_created_at: Optional[datetime] = Field(default=None)
    synced_at: Optional[datetime] = Field(default=None)
    device_id: Optional[str] = Field(default=None, max_length=100)

    processing_attempts: int = Field(default=0)
    max_attempts: int = Field(default=3)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    wound_detections: List["Detection"] = Relationship(
        back_populates="wound_analysis",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @property
    def is_guest_analysis(self) -> bool:
        return self.user_id is None and self.guest_session_id is not None

    @classmethod
    def create_analysis(
        cls,
        image_url: str,
        image_size_bytes: Optional[int] = None,
        user_id: Optional[uuid.UUID] = None,
        guest_session_id: Optional[uuid.UUID] = None
    ) -> "Analysis":
        
        if user_id is None and guest_session_id is None:
            raise ValueError("Phải cung cấp user_id hoặc guest_session_id để phân tích vết thương") 
        
        if user_id is not None and guest_session_id is not None:
            raise ValueError(
                "Không thể cung cấp cả user_id và guest_session_id."
                "Sử dụng user_id cho người dùng được xác thực, guest_session_id cho khách."
            )

        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        return cls(
            user_id=user_id,
            guest_session_id=guest_session_id,
            image_url=image_url,
            image_size_bytes=image_size_bytes,
            queued_at=current_time,
            created_at=current_time,
            updated_at=current_time,
        )

    def __repr__(self) -> str:
        identifier = f"user={self.user_id}" if self.user_id else f"session={self.guest_session_id}"
        return f"<Analysis({identifier})>"