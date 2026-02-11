"""
Auth API Schemas — Request/Response models used in endpoints.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.modules.auth.schemas.domain import Token, UserBase


# ── Response Models ──────────────────────────────────────────────────────────


class UserResponse(BaseModel):
    """User response schema."""

    user_id: uuid.UUID
    user_name: str
    email: EmailStr

    is_active: bool = Field(
        default=True,
        description="Trạng thái tài khoản người dùng",
    )
    is_verified: bool
    is_deleted: bool = Field(
        default=False,
        description="Soft delete flag. True nếu tài khoản đã bị xóa mềm.",
    )

    created_at: datetime
    updated_at: Optional[datetime] = None

    full_name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    avatar_url: Optional[str] = None
    roles: List[str] = Field(
        default_factory=list,
        description="Danh sách các vai trò được gán cho người dùng",
    )

    class Config:
        from_attributes = True


class TokenResponse(Token):
    """Token response including user info."""

    user: UserResponse


class PasswordResetResponse(BaseModel):
    message: str
    success: bool


class ChangePasswordResponse(BaseModel):
    message: str
    success: bool


# ── Request Models ───────────────────────────────────────────────────────────


class UserCreate(UserBase):
    """Signup request."""

    user_name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Tên người dùng phải từ 3-50 ký tự",
    )
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        description="Mật khẩu phải có ít nhất 8 ký tự",
    )
    confirm_password: str = Field(
        ...,
        min_length=8,
        description="Mật khẩu xác nhận phải khớp với mật khẩu",
    )
    gender: Optional[str] = Field(
        None,
        description="Giới tính: nam, nữ hoặc khác",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_passwords_match(cls, values):
        if isinstance(values, dict):
            password = values.get("password")
            confirm_password = values.get("confirm_password")
            if password and confirm_password and password != confirm_password:
                raise ValueError("Mật khẩu không khớp")
        return values


class UserLogin(BaseModel):
    """Login request."""

    user_name: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh Token Request."""

    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Request reset password via email."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm reset password with token."""

    email: EmailStr
    token: str
    new_password: str = Field(
        ...,
        min_length=8,
        description="Mật khẩu mới phải có ít nhất 8 ký tự",
    )
    confirm_password: str = Field(
        ...,
        min_length=8,
        description="Mật khẩu xác nhận phải khớp với mật khẩu mới",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_passwords_match(cls, values):
        if isinstance(values, dict):
            new_password = values.get("new_password")
            confirm_password = values.get("confirm_password")
            if (
                new_password
                and confirm_password
                and new_password != confirm_password
            ):
                raise ValueError("Mật khẩu không khớp")
        return values


class ChangePasswordRequest(BaseModel):
    """Change password (authenticated)."""

    old_password: str = Field(
        ...,
        min_length=8,
        description="Mật khẩu hiện tại",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        description="Mật khẩu mới",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_password_different(cls, values):
        if isinstance(values, dict):
            old_password = values.get("old_password")
            new_password = values.get("new_password")
            if old_password and new_password and old_password == new_password:
                raise ValueError("Mật khẩu mới phải khác mật khẩu cũ")
        return values
