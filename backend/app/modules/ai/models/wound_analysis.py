from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from app.modules.ai.models.wound_detection import WoundDetection


class WoundAnalysis(SQLModel, table=True):
    __tablename__ = "wound_analyses"  # type: ignore

    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.user_id", index=True)

    image_url: str = Field(max_length=500)
    file_name: str = Field(max_length=255)
    file_size: int = Field(gt=0)

    ai_model_version: str = Field(max_length=100, default="YOLOv11_EfficientNetV2_1.0")
    total_detections: int = Field(default=0, ge=0)
    processing_time_ms: int = Field(gt=0)

    primary_wound_type: str = Field(max_length=100)
    primary_severity: str = Field(max_length=50)  # "mild", "moderate", "severe"
    
    primary_firstaidguide_id: Optional[str] = Field(
        default=None,
        nullable=True,
        foreign_key="firstaid_guides.firstaidguide_id"
    )

    firstaid_snapshot: dict = Field(sa_column=Column(JSONB, nullable=False))

    # Timestamps
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted: bool = Field(default=False)

    wound_detections: List["WoundDetection"] = Relationship(
        back_populates="wound_analysis",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @property
    def is_successful_analysis(self) -> bool:
        """Check if analysis was successful."""
        basic_checks = (
            self.total_detections >= 0 and
            self.primary_wound_type in ["wound", "not_wound"] and
            self.primary_severity in ["mild", "moderate", "severe"]
        )
        
        return basic_checks

    @property
    def processing_time_seconds(self) -> float:
        """Get processing time in seconds."""
        return self.processing_time_ms / 1000

    @property
    def has_multiple_wounds(self) -> bool:
        """Check if image has multiple wounds."""
        return self.total_detections > 1

    @property
    def is_wound_detected(self) -> bool:
        """Check if any wound was detected."""
        return self.primary_wound_type == "wound"

    @property
    def average_confidence(self) -> float:

        return 0.0  

    @property
    def meets_accuracy_threshold(self) -> bool:
        return self.average_confidence >= 0.65

    @classmethod
    def create_analysis(
        cls,
        user_id: str,
        image_url: str,
        file_name: str,
        file_size: int,
        ai_model_version: str = "YOLOv11_EfficientNetV2_1.0",
        total_detections: int = 0,
        processing_time_ms: int = 0,
        primary_wound_type: str = "not_wound",
        primary_severity: str = "mild",
        primary_firstaidguide_id: Optional[str] = None,  
        firstaid_snapshot: dict = None,
        analyzed_at: Optional[datetime] = None
    ) -> "WoundAnalysis":
        """Create a new wound analysis với các trường bắt buộc."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        if firstaid_snapshot is None:
            firstaid_snapshot = {
                "title": "Không phát hiện vết thương",
                "description": "Không có hướng dẫn sơ cứu cần thiết",
                "steps": [],
                "warnings": [],
                "dos": [],
                "donts": []
            }

        return cls(
            user_id=user_id,
            image_url=image_url,
            file_name=file_name,
            file_size=file_size,
            ai_model_version=ai_model_version,
            total_detections=total_detections,
            processing_time_ms=processing_time_ms,
            primary_wound_type=primary_wound_type,
            primary_severity=primary_severity,
            primary_firstaidguide_id=primary_firstaidguide_id,
            firstaid_snapshot=firstaid_snapshot,
            analyzed_at=analyzed_at or current_time,
            created_at=current_time,
            updated_at=current_time,
            is_deleted=False
        )

    def update_analysis(
        self,
        total_detections: Optional[int] = None,
        processing_time_ms: Optional[int] = None,
        primary_wound_type: Optional[str] = None,
        primary_severity: Optional[str] = None,
        primary_firstaidguide_id: Optional[str] = None,
        firstaid_snapshot: Optional[dict] = None
    ) -> None:
        """Update analysis information."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        if total_detections is not None:
            self.total_detections = total_detections
        if processing_time_ms is not None:
            self.processing_time_ms = processing_time_ms
        if primary_wound_type is not None:
            self.primary_wound_type = primary_wound_type
        if primary_severity is not None:
            self.primary_severity = primary_severity
        if primary_firstaidguide_id is not None:
            self.primary_firstaidguide_id = primary_firstaidguide_id
        if firstaid_snapshot is not None:
            self.firstaid_snapshot = firstaid_snapshot

        self.updated_at = current_time

    def mark_as_deleted(self) -> None:
        """Soft delete the analysis."""
        self.is_deleted = True
        self.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    def to_response_dict(self) -> dict:
        """Convert analysis to response dictionary."""
        return {
            "analysis_id": self.analysis_id,
            "user_id": self.user_id,
            "image_url": self.image_url,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "ai_model_version": self.ai_model_version,
            "total_detections": self.total_detections,
            "processing_time_ms": self.processing_time_ms,
            "processing_time_seconds": round(self.processing_time_seconds, 3) if self.processing_time_ms > 0 else None,
            "primary_wound_type": self.primary_wound_type,
            "primary_severity": self.primary_severity,
            "primary_firstaidguide_id": self.primary_firstaidguide_id,  
            "firstaid_snapshot": self.firstaid_snapshot,
            "analyzed_at": self.analyzed_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_deleted": self.is_deleted,
            
            # Computed properties
            "is_successful_analysis": self.is_successful_analysis,
            "has_multiple_wounds": self.has_multiple_wounds,
            "is_wound_detected": self.is_wound_detected,
            "average_confidence": self.average_confidence,  
            "meets_accuracy_threshold": self.meets_accuracy_threshold,  
        }