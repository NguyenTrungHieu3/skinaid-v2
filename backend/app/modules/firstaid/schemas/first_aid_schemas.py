from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import uuid

class CreateFirstAidGuideRequest(BaseModel):
    wound_type: str = Field(..., description="Loại vết thương (abrasion, bruise, burn, cut)")
    severity: str = Field(..., description="Mức độ (mild, moderate, severe)")
    sub_type: Optional[str] = Field(None, description="Loại phụ (chỉ cho burn: blister, skintear)")
    title: str = Field(..., min_length=5, max_length=200, description="Tiêu đề hướng dẫn")
    description: Optional[str] = Field(None, max_length=1000, description="Mô tả chi tiết")
    
    steps: List[str] = Field(..., min_items=1, description="Các bước thực hiện")
    warnings: Optional[List[str]] = Field(default=None, description="Cảnh báo")
    dos: Optional[List[str]] = Field(default=None, description="Những việc nên làm")
    donts: Optional[List[str]] = Field(default=None, description="Những việc không nên làm")
    supplies_needed: Optional[List[str]] = Field(default=None, description="Vật dụng cần thiết")
    
    estimated_healing_time: Optional[str] = Field(None, max_length=100, description="Thời gian phục hồi")
    
    @validator('wound_type')
    def validate_wound_type(cls, v):
        valid_types = ['abrasion', 'bruise', 'burn', 'cut']
        if v.lower() not in valid_types:
            raise ValueError(f'wound_type must be one of {valid_types}')
        return v.lower()
    
    @validator('severity')
    def validate_severity(cls, v):
        valid_severities = ['mild', 'moderate', 'severe']
        if v.lower() not in valid_severities:
            raise ValueError(f'severity must be one of {valid_severities}')
        return v.lower()
    
    @validator('sub_type')
    def validate_sub_type(cls, v, values):
        if v:
            wound_type = values.get('wound_type', '').lower()
            if wound_type != 'burn':
                raise ValueError('sub_type only allowed for burn wounds')
            valid_subtypes = ['blister', 'skintear']
            if v.lower() not in valid_subtypes:
                raise ValueError(f'sub_type for burn must be one of {valid_subtypes}')
            return v.lower()
        return v

class UpdateFirstAidGuideRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200, description="Tiêu đề")
    description: Optional[str] = Field(None, max_length=1000, description="Mô tả")
    
    steps: Optional[List[str]] = Field(None, description="Các bước thực hiện")
    warnings: Optional[List[str]] = Field(None, description="Cảnh báo")
    dos: Optional[List[str]] = Field(None, description="Những việc nên làm")
    donts: Optional[List[str]] = Field(None, description="Những việc không nên làm")
    supplies_needed: Optional[List[str]] = Field(None, description="Vật dụng cần thiết")
    
    estimated_healing_time: Optional[str] = Field(None, max_length=100, description="Thời gian phục hồi")
    is_active: Optional[bool] = Field(None, description="Trạng thái hoạt động")

class FirstAidGuideResponse(BaseModel):
    firstaidguide_id: uuid.UUID = Field(..., description="ID hướng dẫn sơ cứu")
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

    created_by: Optional[uuid.UUID] = Field(None, description="Người tạo")
    created_at: datetime = Field(..., description="Ngày tạo")
    updated_at: datetime = Field(..., description="Ngày cập nhật cuối")

    has_complete_instructions: bool = Field(..., description="Có đầy đủ hướng dẫn")
    instructions_count: int = Field(..., description="Số bước hướng dẫn")
    supplies_count: int = Field(..., description="Số vật dụng cần thiết")

class WoundTypeResponse(BaseModel):
    wound_type: str = Field(..., description="Loại vết thương")
    severities: List[str] = Field(..., description="Các mức độ có sẵn")