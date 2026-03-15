from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    user_name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username must be 3-50 characters",
    )
    email: EmailStr


class Token(BaseModel):

    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
