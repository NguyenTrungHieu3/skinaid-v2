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
    user_id: str = Field(..., description="Wound history ID")
    file_name: str = Field(..., description="File name")
    file_path: str = Field(..., description="File path")
    file_size: int = Field(..., description="File size")
    file_type: str = Field(..., description="File type")
    width: int = Field(..., description="Image width")
    height: int = Field(..., description="Image height")
    upload_status: str = Field(..., description="Upload status")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Update time")

class WoundImageDetail(ImageUploadResponse):
    error_message: Optional[str] = Field(None, description="Error message if any")

class UploadSuccessResponse(SuccessResponse[WoundImageDetail]):
    pass

class UploadErrorResponse(ErrorResponse):
    pass