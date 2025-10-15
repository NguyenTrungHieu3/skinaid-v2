from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING, Dict, Any
from app.shared.models.basemodel import TimestampMixin
import uuid

if TYPE_CHECKING:
    from app.modules.auth.models.user import User

class AIAnalysisResult(SQLModel, TimestampMixin, table=True):
    __tablename__ = "ai_analysis_results"

    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.user_id", index=True)

    image_path: str = Field(index=True)
    image_size: Optional[Dict[str, int]] = Field(default=None, sa_column_kwargs={"type_": "JSON"})

    num_detections: int = Field(default=0)
    detections: Dict[str, Any] = Field(default_factory=dict, sa_column_kwargs={"type_": "JSON"})
    processing_time: Optional[float] = Field(default=None)

    ai_model_version: Optional[str] = Field(default=None)
    confidence_threshold: Optional[float] = Field(default=0.5)

    is_success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None)
    error_code: Optional[str] = Field(default=None)

    user: Optional["User"] = Relationship(back_populates="ai_analyses")

class AIAnalysisRequest(SQLModel):
    """Model cho yêu cầu phân tích AI"""
    image_path: str
    confidence_threshold: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)
    return_visualization: Optional[bool] = Field(default=False)

class AIDetectionResult(SQLModel):
    """Model cho một detection result"""
    class_name: str
    confidence: float
    bbox: Dict[str, int]  # x, y, width, height
    severity: str

class AIBatchAnalysisRequest(SQLModel):
    """Model cho batch analysis request"""
    image_paths: List[str]
    confidence_threshold: Optional[float] = Field(default=0.5)
    batch_size: Optional[int] = Field(default=10)

class AIModelInfo(SQLModel):
    """Model thông tin mô hình AI"""
    model_name: str
    version: str
    framework: str
    input_size: Dict[str, int]
    classes: List[str]
    last_updated: datetime
    accuracy: Optional[float] = None