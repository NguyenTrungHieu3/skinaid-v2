from pydantic import BaseModel, Field
from typing import List

class BoundingBox(BaseModel):
    x: int = Field(..., description="Top-left X coordinate")
    y: int = Field(..., description="Top-left Y coordinate")
    width: int = Field(..., description="Box width")
    height: int = Field(..., description="Box height")

class Detection(BaseModel):
    class_name: str = Field(..., description="Wound type (burn, abrasion, etc.)")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence (0-1)")
    bbox: BoundingBox
    severity: str = Field(..., description="Severity level (mild, moderate, severe)")

class ImageSize(BaseModel):
    width: int
    height: int

class DetectionResponse(BaseModel):
    success: bool
    num_detections: int = Field(..., description="Number of wounds detected")
    detections: List[Detection]
    image_size: ImageSize
    processing_time: float = Field(..., description="Processing time in seconds")
    ai_model_version: str = Field(default="YOLOv11_v1.0")