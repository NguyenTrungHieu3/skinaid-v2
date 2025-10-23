from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UUID
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

class GuestAnalysis(SQLModel, table=True):
    __tablename__ = "guest_analyses"

    analysis_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="guest_sessions.session_id")
    upload_id: Optional[uuid.UUID] = Field(default=None, foreign_key="guest_uploads.upload_id")

    wound_type: Optional[str] = Field(default=None, max_length=50)
    severity: Optional[str] = Field(default=None, max_length=50)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    result_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted: bool = Field(default=False)