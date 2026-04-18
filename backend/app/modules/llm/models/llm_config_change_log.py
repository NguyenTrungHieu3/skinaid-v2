from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy import ForeignKey
from uuid import uuid4, UUID
from typing import Optional, Dict, Any
from datetime import datetime, timezone


class LLMConfigChangeLog(SQLModel, table=True):
    """Audit trail for every LLM configuration change."""

    __tablename__ = "llm_config_change_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    config_id: UUID = Field(
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("llm_configurations.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    changed_by: Optional[UUID] = Field(
        default=None,
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # model_change | param_update | activate | deactivate | maintenance_on | maintenance_off
    change_type: str = Field(max_length=30)

    old_values: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    new_values: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    reason: Optional[str] = Field(default=None)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
