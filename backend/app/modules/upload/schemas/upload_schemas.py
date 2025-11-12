import re
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.core.config import settings

MAX_FILE_SIZE = getattr(settings, "MAX_UPLOAD_SIZE", 5 * 1024 * 1024)

ALLOWED_MIME_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png']
}

ALLOWED_PURPOSES = ['general', 'avatar', 'skin_analysis']

class UploadParams(BaseModel):

    purpose: str = Field(default='general', description="Mục đích tải lên tệp (general/avatar/skin_analysis)")
    quality: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Chất lượng JPEG (1-100), để trống để dùng giá trị mặc định an toàn của hệ thống"
    )

    @field_validator('purpose')
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        if v not in ALLOWED_PURPOSES:
            raise ValueError(f"Mục đích tải lên không hợp lệ. Hợp lệ: {', '.join(ALLOWED_PURPOSES)}")
        return v

class ValidationResult(BaseModel):

    is_valid: bool = Field(..., description="Tệp hợp lệ hay không sau khi kiểm tra")
    errors: List[str] = Field(default_factory=list, description="Danh sách lỗi khiến tệp không hợp lệ")
    warnings: List[str] = Field(default_factory=list, description="Danh sách cảnh báo (không chặn tải lên)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": ["Ảnh lớn, sẽ được tự động resize để tối ưu xử lý"]
            }
        }
    )

class UploadResponse(BaseModel):
    
    # Thông tin cơ bản về tệp đã tải lên
    file_url: str = Field(..., description="URL công khai để truy cập tệp đã tải lên")
    file_name: str = Field(..., description="Tên tệp được lưu trên máy chủ")
    file_size: int = Field(..., description="Kích thước tệp (bytes) sau xử lý/lưu trữ")
    mime_type: str = Field(..., description="MIME type thực tế của tệp đã lưu")
    
    # Thông tin bổ sung phục vụ kiểm tra và debug
    checksum: Optional[str] = Field(None, description="Giá trị SHA256 checksum để đối chiếu toàn vẹn dữ liệu")
    warnings: Optional[List[str]] = Field(None, description="Danh sách cảnh báo liên quan tới tệp (nếu có)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_url": "http://localhost:8000/uploads/users/123/general/20240101_abc.jpg",
                "file_name": "20240101_abc.jpg",
                "file_size": 875000,
                "mime_type": "image/jpeg",
                "checksum": "abc123...",
                "warnings": ["Ảnh đã được resize và nén để tối ưu lưu trữ"]
            }
        }
    )
