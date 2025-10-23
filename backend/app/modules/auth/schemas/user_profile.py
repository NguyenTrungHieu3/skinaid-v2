from pydantic import BaseModel
from typing import Optional
from datetime import date
import uuid


class UserProfileBase(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None  
    address: Optional[str] = None
    avatar_url: Optional[str] = None


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileResponse(UserProfileBase):
    user_id: uuid.UUID
    created_at: Optional[str] = None
    updated_at: Optional[str] = None