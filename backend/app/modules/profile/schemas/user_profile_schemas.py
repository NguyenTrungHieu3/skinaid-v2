from pydantic import BaseModel, Field
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

class AvatarUploadResponse(BaseModel):
    url: str = Field(..., description="Đường dẫn URL của ảnh vừa upload")