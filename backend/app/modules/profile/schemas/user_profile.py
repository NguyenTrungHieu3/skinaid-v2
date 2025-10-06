from pydantic import BaseModel
from typing import Optional
from datetime import date


class UserProfileBase(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None  # Changed from GenderEnum to str
    address: Optional[str] = None
    avatar_url: Optional[str] = None


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileResponse(UserProfileBase):
    pass