from sqlmodel import SQLModel, Field
from typing import Optional, Dict, List
import uuid
from datetime import datetime, timezone


class ModelResult(SQLModel, table=True):
    __tablename__ = "model_result"

    model_result_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    wound_images_id: str = Field(foreign_key="image_information.wound_images_id")
    wound_type: str
    confidence_score: float = Field(ge=0, le=1)
    severity: str  # public."severity_enum"
    ai_model_version: str
    processing_time_ms: int = Field(ge=0)
    processed_at: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    @property
    def severity_display(self) -> str:
        """Get severity in Vietnamese display format."""
        severity_map = {
            "mild": "Nhẹ",
            "moderate": "Trung bình",
            "severe": "Nặng"
        }
        return severity_map.get(self.severity.lower(), self.severity)

    @property
    def confidence_percentage(self) -> float:
        """Get confidence as percentage."""
        return self.confidence_score * 100

    @property
    def processing_time_seconds(self) -> float:
        """Get processing time in seconds."""
        return self.processing_time_ms / 1000

    @property
    def is_high_confidence(self) -> bool:
        """Check if result has high confidence (> 0.8)."""
        return self.confidence_score > 0.8

    @property
    def is_reliable(self) -> bool:
        """Check if result is reliable (> 0.6)."""
        return self.confidence_score > 0.6

    @property
    def is_fast_processing(self) -> bool:
        """Check if processing was fast (< 2 seconds)."""
        return self.processing_time_seconds < 2.0

    @classmethod
    def create_result(
        cls,
        wound_images_id: str,
        wound_type: str,
        confidence_score: float,
        severity: str,
        ai_model_version: str,
        processing_time_ms: int,
        processed_at: Optional[datetime] = None
    ) -> "ModelResult":
        """Create a new model result."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        return cls(
            wound_images_id=wound_images_id,
            wound_type=wound_type,
            confidence_score=confidence_score,
            severity=severity,
            ai_model_version=ai_model_version,
            processing_time_ms=processing_time_ms,
            processed_at=processed_at or current_time,
            created_at=current_time,
            updated_at=current_time
        )

    def update_result(
        self,
        confidence_score: Optional[float] = None,
        severity: Optional[str] = None,
        processing_time_ms: Optional[int] = None
    ) -> None:
        """Update result information."""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        if confidence_score is not None:
            self.confidence_score = confidence_score
        if severity is not None:
            self.severity = severity
        if processing_time_ms is not None:
            self.processing_time_ms = processing_time_ms

        self.updated_at = current_time

    def to_response_dict(self) -> dict:
        """Convert result to response dictionary."""
        return {
            "model_result_id": self.model_result_id,
            "wound_images_id": self.wound_images_id,
            "wound_type": self.wound_type,
            "confidence_score": self.confidence_score,
            "confidence_percentage": round(self.confidence_percentage, 2),
            "severity": self.severity,
            "severity_display": self.severity_display,
            "ai_model_version": self.ai_model_version,
            "processing_time_ms": self.processing_time_ms,
            "processing_time_seconds": round(self.processing_time_seconds, 3),
            "processed_at": self.processed_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_high_confidence": self.is_high_confidence,
            "is_reliable": self.is_reliable,
            "is_fast_processing": self.is_fast_processing
        }

class AIDetectionResult(SQLModel):
    """Model cho một detection result"""
    class_name: str
    confidence: float
    bbox: Dict[str, int]  # x, y, width, height
    severity: str

    @property
    def severity_display(self) -> str:
        """Get severity in Vietnamese display format."""
        severity_map = {
            "mild": "Nhẹ",
            "moderate": "Trung bình",
            "severe": "Nặng"
        }
        return severity_map.get(self.severity.lower(), self.severity)

    @property
    def confidence_percentage(self) -> float:
        """Get confidence as percentage."""
        return self.confidence * 100

    @property
    def is_high_confidence(self) -> bool:
        """Check if detection has high confidence (> 0.8)."""
        return self.confidence > 0.8

    @property
    def is_reliable(self) -> bool:
        """Check if detection is reliable (> 0.6)."""
        return self.confidence > 0.6

    def to_dict(self) -> dict:
        """Convert detection result to dictionary."""
        return {
            "class_name": self.class_name,
            "confidence": self.confidence,
            "confidence_percentage": round(self.confidence_percentage, 2),
            "severity": self.severity,
            "severity_display": self.severity_display,
            "bbox": self.bbox,
            "is_high_confidence": self.is_high_confidence,
            "is_reliable": self.is_reliable
        }


class AIModelInfo(SQLModel):
    """Model thông tin mô hình AI"""
    detection_model: str
    classification_model: str
    num_wound_classes: int
    wound_classes: List[str]

    @property
    def total_classes(self) -> int:
        """Get total number of wound classes."""
        return len(self.wound_classes)

    @property
    def supports_detection(self) -> bool:
        """Check if model supports detection."""
        return bool(self.detection_model and self.detection_model.strip())

    @property
    def supports_classification(self) -> bool:
        """Check if model supports classification."""
        return bool(self.classification_model and self.classification_model.strip())

    def has_wound_class(self, wound_class: str) -> bool:
        """Check if model supports specific wound class."""
        return wound_class.lower() in [wc.lower() for wc in self.wound_classes]

    def get_supported_classes_display(self) -> str:
        """Get supported classes as formatted string."""
        if not self.wound_classes:
            return "Không có thông tin"

        return ", ".join(self.wound_classes)

    def to_dict(self) -> dict:
        """Convert model info to dictionary."""
        return {
            "detection_model": self.detection_model,
            "classification_model": self.classification_model,
            "num_wound_classes": self.num_wound_classes,
            "total_classes": self.total_classes,
            "wound_classes": self.wound_classes,
            "supported_classes_display": self.get_supported_classes_display(),
            "supports_detection": self.supports_detection,
            "supports_classification": self.supports_classification
        }