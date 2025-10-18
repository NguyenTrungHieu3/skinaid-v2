from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from app.modules.ai.models.wound_analysis import WoundAnalysis


class WoundDetection(SQLModel, table=True):
    __tablename__ = "wound_detections"  # type: ignore

    detection_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    analysis_id: str = Field(foreign_key="wound_analyses.analysis_id", index=True)

    wound_type: str = Field(max_length=100)
    severity: str = Field(max_length=50)     # Mức độ: mild, moderate, severe
    confidence_score: float = Field(ge=0.0, le=1.0)  # Độ tin cậy từ 0-1

    bounding_box: dict = Field(sa_column=Column(JSONB, nullable=False))

    detection_index: int = Field(default=0, ge=0)
    is_primary: bool = Field(default=False)         # Là detection chính hay không
    
    firstaidguide_id: Optional[str] = Field(
        default=None,
        nullable=True,
        foreign_key="firstaid_guides.firstaidguide_id"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    wound_analysis: Optional["WoundAnalysis"] = Relationship(back_populates="wound_detections")

    @property
    def confidence_percentage(self) -> Optional[float]:
        """Get confidence as percentage."""
        return self.confidence_score * 100 if self.confidence_score is not None else None

    @property
    def is_high_confidence(self) -> bool:
        """Check if detection has high confidence (> 0.8)."""
        return self.confidence_score > 0.8

    @property
    def is_reliable(self) -> bool:
        """Check if detection is reliable (> 0.65 - theo yêu cầu AI_Guidelines)."""
        return self.confidence_score > 0.65

    @property
    def meets_accuracy_threshold(self) -> bool:
        """Check if detection meets minimum accuracy requirement (≥ 65%)."""
        return self.confidence_score >= 0.65

    @property
    def bounding_box_area(self) -> Optional[float]:
        """Calculate bounding box area if available."""
        if not self.bounding_box:
            return None

        try:
            width = self.bounding_box.get("width", 0)
            height = self.bounding_box.get("height", 0)
            return width * height
        except (KeyError, TypeError):
            return None

    @property
    def severity_level(self) -> str:
        """Get severity level as readable string."""
        severity_map = {
            "mild": "Nhẹ",
            "moderate": "Trung bình",
            "severe": "Nặng"
        }
        return severity_map.get(self.severity.lower() if self.severity else "", "Không xác định")

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
        """Create a new wound detection với các trường bắt buộc."""
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

    def update_detection(
        self,
        wound_type: Optional[str] = None,
        severity: Optional[str] = None,
        confidence_score: Optional[float] = None,
        bounding_box: Optional[dict] = None,
        is_primary: Optional[bool] = None,
        firstaidguide_id: Optional[str] = None
    ) -> None:
        """Update detection information."""
        if wound_type is not None:
            self.wound_type = wound_type
        if severity is not None:
            self.severity = severity
        if confidence_score is not None:
            self.confidence_score = confidence_score
        if bounding_box is not None:
            self.bounding_box = bounding_box
        if is_primary is not None:
            self.is_primary = is_primary
        if firstaidguide_id is not None:
            self.firstaidguide_id = firstaidguide_id

    def mark_as_primary(self) -> None:
        """Mark this detection as the primary wound."""
        self.is_primary = True

    def unmark_as_primary(self) -> None:
        """Unmark this detection as primary."""
        self.is_primary = False

    def to_response_dict(self) -> dict:
        """Convert detection to response dictionary."""
        return {
            "detection_id": self.detection_id,
            "analysis_id": self.analysis_id,
            "wound_type": self.wound_type,
            "severity": self.severity,
            "severity_display": self.severity_level,
            "confidence_score": self.confidence_score,
            "confidence_percentage": round(self.confidence_percentage, 2) if self.confidence_percentage else None,
            "bounding_box": self.bounding_box,
            "bounding_box_area": self.bounding_box_area,
            "detection_index": self.detection_index,
            "is_primary": self.is_primary,
            "firstaidguide_id": self.firstaidguide_id,
            "created_at": self.created_at,
            "is_high_confidence": self.is_high_confidence,
            "is_reliable": self.is_reliable
        }