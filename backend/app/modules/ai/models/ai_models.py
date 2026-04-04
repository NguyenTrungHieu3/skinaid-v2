from sqlmodel import SQLModel, Field
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID


class AIModel(SQLModel, table=True):
    __tablename__ = "ai_models"
    __table_args__ = (
        UniqueConstraint("stage", "version", name="ai_models_stage_version_key"),
    )

    model_id: UUID = Field(default_factory=uuid4, primary_key=True)

    stage: str = Field(max_length=20)
    model_name: str = Field(max_length=100)
    version: str = Field(max_length=50)
    description: Optional[str] = Field(default=None)

    file_path: str = Field(max_length=500)
    file_size_mb: Optional[float] = Field(default=None)
    
    file_format: Optional[str] = Field(default=None, max_length=20)
    checksum_sha256: Optional[str] = Field(default=None, max_length=64)

    accuracy: Optional[float] = Field(default=None)
    metrics: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    is_active: bool = Field(default=False, index=True)
    is_beta: bool = Field(default=False)
    traffic_percentage: int = Field(default=0, ge=0, le=100)

    deployed_at: Optional[datetime] = Field(default=None)
    deployed_by: Optional[UUID] = Field(default=None, foreign_key="users.user_id")
    rollback_to_model_id: Optional[UUID] = Field(
        default=None, foreign_key="ai_models.model_id"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
