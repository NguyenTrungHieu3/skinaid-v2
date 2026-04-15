from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy import ForeignKey
from uuid import uuid4, UUID
from typing import Optional
from datetime import datetime, timezone


class LLMConfiguration(SQLModel, table=True):
    """Runtime LLM configuration — DB values override .env defaults."""

    __tablename__ = "llm_configurations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    config_key: str = Field(max_length=50, unique=True, index=True)
    display_name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None)

    model_name: str = Field(max_length=100)

    temperature: float = Field(default=0.3)
    max_tokens: int = Field(default=2000)
    top_k: int = Field(default=5)

    is_active: bool = Field(default=True)
    is_maintenance: bool = Field(default=False)
    maintenance_message: Optional[str] = Field(default=None)

    updated_by: Optional[UUID] = Field(
        default=None,
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
