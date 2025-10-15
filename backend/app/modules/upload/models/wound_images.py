from sqlmodel import SQLModel, Field, Column
from sqlalchemy import String
from typing import Optional
from datetime import datetime
from app.shared.models.basemodel import TimestampMixin
import uuid

class WoundImages(SQLModel, TimestampMixin, table=True):
    __tablename__ = "wound_images"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.user_id", index=True)

    # File information
    file_name: str
    file_path: str = Field(unique=True)  # Unique để tránh trùng
    file_size: int = Field(gt=0)
    file_type: str
    width: Optional[int] = Field(default=None, gt=0)
    height: Optional[int] = Field(default=None, gt=0)

    # Upload status
    upload_status: str = Field(
        default="pending",
        sa_column=Column(String(20))
    )

    # AI Results
    wound_type: Optional[str] = Field(default=None)
    confidence_score: Optional[float] = Field(default=None, ge=0, le=1)
    severity: Optional[str] = Field(default=None)  # mild/moderate/severe
    ai_model_version: Optional[str] = Field(default=None)
    processing_time_ms: Optional[int] = Field(default=None, ge=0)

    error_message: Optional[str] = Field(default=None)

    # Timestamps
    processed_at: Optional[datetime] = None

    def __init__(self, **data): 
        if 'upload_status' not in data: 
            data['upload_status'] = 'pending'
        super().__init__(**data)