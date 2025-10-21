from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
class FirstAidGuideResponse(BaseModel):
    firstaidguide_id: str = Field(..., description="ID hướng dẫn sơ cứu")
    wound_type: str = Field(..., description="Loại vết thương")
    severity: str = Field(..., description="Mức độ nghiêm trọng")
    sub_type: Optional[str] = Field(None, description="Loại phụ (chỉ dành cho burn)")
    severity_display: str = Field(..., description="Tên mức độ tiếng Việt")
    title: str = Field(..., description="Tiêu đề hướng dẫn")
    description: Optional[str] = Field(None, description="Mô tả chi tiết")

    steps: Optional[List[str]] = Field(None, description="Các bước thực hiện")
    warnings: Optional[List[str]] = Field(None, description="Cảnh báo")
    dos: Optional[List[str]] = Field(None, description="Những việc nên làm")
    donts: Optional[List[str]] = Field(None, description="Những việc không nên làm")
    supplies_needed: Optional[List[str]] = Field(None, description="Vật dụng cần thiết")

    estimated_healing_time: Optional[str] = Field(None, description="Thời gian phục hồi dự kiến")
    is_active: bool = Field(..., description="Hướng dẫn còn hiệu lực")
    version: int = Field(..., description="Phiên bản")

    created_by: Optional[str] = Field(None, description="Người tạo")
    created_at: datetime = Field(..., description="Ngày tạo")
    updated_at: datetime = Field(..., description="Ngày cập nhật cuối")

    has_complete_instructions: bool = Field(..., description="Có đầy đủ hướng dẫn")
    instructions_count: int = Field(..., description="Số bước hướng dẫn")
    supplies_count: int = Field(..., description="Số vật dụng cần thiết")

class WoundTypeResponse(BaseModel):
    wound_type: str = Field(..., description="Loại vết thương")
    severities: List[str] = Field(..., description="Các mức độ có sẵn")