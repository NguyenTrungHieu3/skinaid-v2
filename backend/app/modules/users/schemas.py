from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class ScanHistoryItem(BaseModel):
    id: UUID
    created_at: datetime
    wound_type: Optional[str]
    severity: Optional[str]
    image_url: str

class UserListItem(BaseModel):
    id: str  # user_id as string
    full_name: Optional[str] = None
    email: str
    role: str
    status: str
    uploads_count: int = 0
    join_date: datetime
    last_active_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[UserListItem]

class UserDetailResponse(UserListItem):
    scan_history: List[ScanHistoryItem] = []

class UpdateUserStatusRequest(BaseModel):
    status: str
    
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ["active", "inactive"]:
            raise ValueError("status must be active or inactive")
        return v

class UpdateUserStatusResponse(BaseModel):
    id: str
    status: str
    updated_at: datetime
