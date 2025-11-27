from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class CreateUserRequest(BaseModel):
    email: EmailStr 
    display_name: str
    password: str
    role: str
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed_roles = ['user', 'admin']
        if v.lower() not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v.lower()

class UpdateUserRequest(BaseModel):
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_roles = ['user', 'admin']
            if v.lower() not in allowed_roles:
                raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
            return v.lower()
        return v

class UpdateUserStatusRequest(BaseModel):
    is_active: bool

# ===================== RESPONSE SCHEMAS =====================

class UserRoleInfo(BaseModel):
    role_name: str
    role_display_name: Optional[str] = None


class UserBasicInfo(BaseModel):
    user_id: UUID
    email: str
    display_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    roles: List[str] = []
    upload_count: int = 0
    
    class Config:
        from_attributes = True


class UserDetailInfo(BaseModel):
    user_id: UUID
    email: str
    display_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    roles: List[str] = []
    upload_count: int = 0
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    total: int = Field(..., description="Total number of records")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Records per page")
    total_pages: int = Field(..., description="Total number of pages")


class UserListResponse(BaseModel):
    """Response schema for user list"""
    users: List[UserBasicInfo]
    pagination: PaginationInfo
    
    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "john.smith@email.com",
                        "display_name": "John Smith",
                        "is_active": True,
                        "is_verified": True,
                        "created_at": "2024-01-15T10:30:00",
                        "roles": ["user"],
                        "upload_count": 23
                    }
                ],
                "pagination": {
                    "total": 100,
                    "page": 1,
                    "limit": 10,
                    "total_pages": 10
                }
            }
        }


class UserDetailResponse(BaseModel):
    """Response schema for user detail"""
    user: UserDetailInfo
    
    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "john.smith@email.com",
                    "display_name": "John Smith",
                    "is_active": True,
                    "is_verified": True,
                    "created_at": "2024-01-15T10:30:00",
                    "updated_at": "2024-01-15T10:30:00",
                    "roles": ["user"],
                    "upload_count": 23,
                    "last_login": "2024-10-30T08:45:00"
                }
            }
        }


class UserStatsResponse(BaseModel):
    """User statistics response"""
    total_users: int
    active_users: int
    verified_users: int
    users_by_role: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_users": 150,
                "active_users": 142,
                "verified_users": 138,
                "users_by_role": {
                    "user": 135,
                    "moderator": 10,
                    "admin": 5
                }
            }
        }
