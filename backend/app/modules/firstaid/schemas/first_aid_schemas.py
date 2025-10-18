from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class FirstAidInstruction(BaseModel):
    do: List[str] = Field(..., description="Những việc nên làm")
    dont: List[str] = Field(..., description="Những việc không nên làm")

class FirstAidInformation(BaseModel):
    cause: Optional[str] = Field(None, description="Nguyên nhân gây vết thương")
    symptoms: Optional[str] = Field(None, description="Triệu chứng")
    risks: Optional[str] = Field(None, description="Rủi ro liên quan")

class FirstAidGuideResponse(BaseModel):
    firstaidguide_id: str = Field(..., description="ID hướng dẫn sơ cứu")
    wound_type: str = Field(..., description="Loại vết thương")
    severity: str = Field(..., description="Mức độ nghiêm trọng")
    severity_display: str = Field(..., description="Tên mức độ tiếng Việt")
    title: str = Field(..., description="Tiêu đề hướng dẫn")
    description: Optional[str] = Field(None, description="Mô tả chi tiết")

    steps: Optional[Dict[str, Any]] = Field(None, description="Các bước thực hiện")
    warnings: Optional[Dict[str, Any]] = Field(None, description="Cảnh báo")
    dos: Optional[Dict[str, Any]] = Field(None, description="Những việc nên làm")
    donts: Optional[Dict[str, Any]] = Field(None, description="Những việc không nên làm")
    supplies_needed: Optional[Dict[str, Any]] = Field(None, description="Vật dụng cần thiết")

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

class FirstAidSearchResponse(BaseModel):
    results: List[FirstAidGuideResponse] = Field(..., description="Danh sách hướng dẫn sơ cứu")
    total: int = Field(..., description="Tổng số kết quả")
    limit: int = Field(..., description="Số lượng tối đa")