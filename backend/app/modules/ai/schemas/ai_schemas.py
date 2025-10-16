from pydantic import BaseModel, Field
from typing import List, Optional

class BoundingBox(BaseModel):
    x: float = Field(..., description="Top-left X coordinate")
    y: float = Field(..., description="Top-left Y coordinate")
    width: float = Field(..., description="Box width")
    height: float = Field(..., description="Box height")

class AIDetectionResult(BaseModel):
    class_name: str = Field(..., description="Wound type (burn, abrasion, etc.)")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence (0-1)")
    bbox: BoundingBox
    severity: str = Field(..., description="Severity level (mild, moderate, severe)")

class AIAnalysisResult(BaseModel):
    success: bool
    num_detections: int = Field(..., description="Number of wounds detected")
    detections: List[AIDetectionResult] = Field(..., description="Detections")
    image_size: Optional[dict] = Field(None, description="Image size information")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    ai_model_version: Optional[str] = Field(None, description="AI model version")
    error: Optional[str] = Field(None, description="Error message if any")
    error_code: Optional[str] = Field(None, description="Error code if any")

class AIBatchAnalysisResult(BaseModel):
    results: List[dict] = Field(..., description="Analysis results")
    summary: dict = Field(..., description="Summary")