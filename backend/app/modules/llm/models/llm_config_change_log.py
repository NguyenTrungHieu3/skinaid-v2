from sqlmodel import SQLModel, Field, Column
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from uuid import uuid4, UUID
from typing import Optional, Any
from datetime import datetime, timezone


class LLMConfigChangeLog(SQLModel, table=True):
    """Audit trail entry for LLM configuration changes."""

    __tablename__ = "llm_config_change_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    config_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("llm_configurations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )

    changed_by: Optional[UUID] = Field(
        default=None,
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )

    change_type: str = Field(max_length=30, index=True)

    old_values: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    new_values: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    reason: Optional[str] = Field(default=None)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
