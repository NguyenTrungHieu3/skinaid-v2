from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime
import uuid

class UserProfileBase(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255, description="Họ tên đầy đủ")
    phone: Optional[str] = Field(None, max_length=20, description="Số điện thoại")
    date_of_birth: Optional[date] = Field(None, description="Ngày sinh")
    gender: Optional[str] = Field(None, max_length=50, description="Giới tính (male, female, other)")
    address: Optional[str] = Field(None, description="Địa chỉ")
    avatar_url: Optional[str] = Field(None, max_length=500, description="URL avatar (S3)")

    @field_validator('phone')
    def validate_phone(cls, v):
        if v is None or v == '':
            return v
        
        phone_clean = v.replace(' ', '').replace('-', '')
        
        if not phone_clean.isdigit():
            raise ValueError('Số điện thoại chỉ được chứa số')
        
        if len(phone_clean) < 10 or len(phone_clean) > 11:
            raise ValueError('Số điện thoại phải có 10-11 chữ số')
        
        if not phone_clean.startswith('0'):
            raise ValueError('Số điện thoại phải bắt đầu bằng số 0')
        
        return phone_clean
    
    @field_validator('gender')
    def validate_gender(cls, v):
        if v is None or v == '':
            return v
        
        valid_genders = ['male', 'female', 'other']
        if v.lower() not in valid_genders:
            raise ValueError(f'Giới tính phải là một trong: {', '.join(valid_genders)}')
        
        return v.lower()

    @field_validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        if v is None:
            return v
        
        today = date.today()
        if v > today:
            raise ValueError('Ngày sinh không được lớn hơn ngày hiện tại')
        
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 14:
            raise ValueError('Người dùng phải từ 14 tuổi trở lên')
        
        return v

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfileResponse(UserProfileBase):
    user_id: uuid.UUID = Field(..., description="ID người dùng")
    age: Optional[int] = Field(None, description="Tuổi tính từ ngày sinh")
    gender_display: str = Field(..., description="Giới tính hiển thị tiếng Việt")
    has_complete_profile: bool = Field(..., description="Profile có đầy đủ thông tin")
    profile_completion_percentage: int = Field(..., description="Phần trăm hoàn thành profile")
    created_at: datetime = Field(..., description="Ngày tạo")
    updated_at: datetime = Field(..., description="Ngày cập nhật cuối")

class ProfileStatisticsResponse(BaseModel):
    total_users: int = Field(..., description="Tổng số users")
    users_with_profile: int = Field(..., description="Users có profile")
    complete_profiles: int = Field(..., description="Profiles hoàn chỉnh")
    average_completion: float = Field(..., description="Phần trăm hoàn thành trung bình")
    gender_distribution: dict = Field(..., description="Phân bố theo giới tính")
    age_distribution: dict = Field(..., description="Phân bố theo độ tuổi")