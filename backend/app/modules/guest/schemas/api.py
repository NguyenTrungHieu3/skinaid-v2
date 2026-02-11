import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.modules.guest.schemas.domain import GuestSessionBase


class GuestSessionResponse(GuestSessionBase):
    session_id: uuid.UUID
    created_at: datetime
    expires_at: datetime
    last_activity_at: datetime

    upload_count: int
    analysis_count: int
    is_active: bool

    # Computed properties
    is_expired: bool
    can_upload: bool
    can_analyze: bool
    remaining_uploads: int
    remaining_analyses: int

    class Config:
        from_attributes = True


class CreateGuestSessionRequest(BaseModel):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class GuestStatsResponse(BaseModel):
    total_sessions: int
    active_sessions: int
    total_uploads: int
    total_analyses: int
    converted_users: int
    average_session_duration: float


class ClaimAnalysisRequest(BaseModel):
    analysis_id: uuid.UUID
