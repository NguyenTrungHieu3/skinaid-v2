from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import uuid
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password with at least 8 characters")
    confirm_password: str = Field(..., min_length=8, description="Confirm password must match password")

    @field_validator('confirm_password')
    @classmethod
    def validate_passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v

class UserResponse(BaseModel):
    user_id: str 
    email: EmailStr
    display_name: Optional[str] = None
    is_verified: bool
    created_at: datetime

    # Profile information
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

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

    @field_validator('confirm_password')
    @classmethod
    def validate_passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordResetResponse(BaseModel):
    message: str
    success: bool
