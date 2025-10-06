from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.shared.schemas.response import SuccessResponse, ErrorResponse

class ImageUploadRequest(BaseModel): 
    description: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Description of the wound image"
    )

class ImageUploadResponse(BaseModel): 
    id: str = Field(..., description="Image ID")
    user_id: str = Field(..., description="User ID")
    file_name: str = Field(..., description="File name")
    file_path: str = Field(..., description="File path")
    file_size: int = Field(..., description="File size")
    file_type: str = Field(..., description="File type")
    width: Optional[int] = Field(None, description="Image width")
    height: Optional[int] = Field(None, description="Image height")
    upload_status: str = Field(..., description="Upload status")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Update time")

class WoundImageDetail(ImageUploadResponse): 
    wound_type: Optional[str] = Field(None, description="Type of wound")
    confidence_score: Optional[float] = Field(None, description="Confidence score (0-1)")
    severity: Optional[str] = Field(None, description="Severity level")
    ai_model_version: Optional[str] = Field(None, description="Model version")
    processing_time_ms: Optional[int] = Field(None, description="Processing time (ms)")
    error_message: Optional[str] = Field(None, description="Error message if any")
    processed_at: Optional[datetime] = Field(None, description="Processing completion time")

class UploadSuccessResponse(SuccessResponse[WoundImageDetail]):
    pass

class UploadErrorResponse(ErrorResponse):
    pass