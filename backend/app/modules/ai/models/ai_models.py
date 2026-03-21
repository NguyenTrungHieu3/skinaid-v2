from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID

class AIModel(SQLModel, table=True):
    __tablename__ = "ai_models"

    model_id: UUID = Field(default_factory=uuid4, primary_key=True)
    model_type: str = Field(max_length=50) # 'classification', 'segmentation', 'severity_scoring'
    version_tag: str = Field(max_length=50, unique=True, index=True)
    file_path: Optional[str] = Field(default=None, max_length=500)
    file_size_bytes: Optional[int] = None
    
    metrics: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    is_active: bool = Field(default=False, index=True)
    is_beta: bool = Field(default=False)
    traffic_percentage: int = Field(default=0, ge=0, le=100)
    
    deployed_at: Optional[datetime] = None
    deployed_by: Optional[UUID] = Field(default=None, foreign_key="users.user_id")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
