from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional, List
from sqlalchemy import UUID
import uuid
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password with at least 8 characters")
    confirm_password: str = Field(..., min_length=8, description="Confirm password must match password")

    @model_validator(mode='before')
    @classmethod
    def validate_passwords_match(cls, values):
        if isinstance(values, dict):
            password = values.get('password')
            confirm_password = values.get('confirm_password')
            if password and confirm_password and password != confirm_password:
                raise ValueError('Passwords do not match')
        return values

class UserResponse(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    display_name: Optional[str] = None
    is_active: bool = Field(default=True, description="User account status")
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    roles: List[str] = Field(default_factory=list, description="List of role names assigned to user")

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class EmailVerificationRequest(BaseModel):
    email: EmailStr
    token: str

class EmailVerificationResponse(BaseModel):
    message: str
    is_verified: bool

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    token: str
    new_password: str = Field(..., min_length=8, description="New password with at least 8 characters")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password must match new password")
    @model_validator(mode='before')
    @classmethod
    def validate_passwords_match(cls, values):
        if isinstance(values, dict):
            new_password = values.get('new_password')
            confirm_password = values.get('confirm_password')
            if new_password and confirm_password and new_password != confirm_password:
                raise ValueError('Passwords do not match')
        return values

class PasswordResetResponse(BaseModel):
    message: str
    success: bool

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=8, description= "Mật khẩu hiện tại")
    new_password: str = Field(..., min_length=8, description= "Mật khẩu mới")

    @model_validator(mode='before')
    @classmethod
    def validate_password_different(cls, values):
        if isinstance(values, dict):
            old_password = values.get('old_password')
            new_password = values.get('new_password')
            if old_password and new_password and old_password == new_password:
                raise ValueError('Mật khẩu mới phải khác mật khẩu cũ')
        return values

class ChangePasswordResponse(BaseModel):
    message: str
    success: bool
