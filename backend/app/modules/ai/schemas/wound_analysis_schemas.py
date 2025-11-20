from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
class WoundDetectionResponse(BaseModel):
    """Response schema for wound detection."""
    detection_id: UUID
    wound_type: str
    severity: str
    sub_type: Optional[str] = None
    confidence_score: float
    bounding_box: Dict[str, Any]
    detection_index: int
    firstaid_snapshot: Dict[str, Any]
class WoundAnalysisResponse(BaseModel):
    """Basic wound analysis response."""
    analysis_id: UUID
    user_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    image_url: str
    file_name: str
    total_detections: int
    processing_time_ms: int
    analyzed_at: datetime
    created_at: datetime
class WoundAnalysisDetailResponse(WoundAnalysisResponse):
    """Detailed wound analysis response with detections."""
    detections: List[WoundDetectionResponse] = Field(default_factory=list)
class WoundAnalysisListResponse(BaseModel):
    """List of wound analyses."""
    total: int
    limit: int
    offset: int
    events: List[WoundAnalysisResponse]