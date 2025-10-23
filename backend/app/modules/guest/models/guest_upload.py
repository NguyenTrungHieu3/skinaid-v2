from sqlmodel import SQLModel, Field
from sqlalchemy import UUID
from typing import Optional
from datetime import datetime, timezone
import uuid

class GuestUpload(SQLModel, table=True):
    __tablename__ = "guest_uploads"

    upload_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="guest_sessions.session_id")

    file_path: str
    file_name: str = Field(max_length=255)
    file_size: int = Field(gt=0)
    mime_type: Optional[str] = Field(default=None, max_length=100)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None