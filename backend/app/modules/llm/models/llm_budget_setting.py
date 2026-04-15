from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy import ForeignKey
from uuid import uuid4, UUID
from typing import Optional
from datetime import datetime, timezone


class LLMBudgetSetting(SQLModel, table=True):
    """Singleton budget & pricing settings for LLM cost tracking."""

    __tablename__ = "llm_budget_settings"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    monthly_budget_usd: float = Field(default=0.0)
    price_per_1k_input_tokens: float = Field(default=0.40)
    price_per_1k_output_tokens: float = Field(default=1.60)
    currency: str = Field(default="USD", max_length=10)

    updated_by: Optional[UUID] = Field(
        default=None,
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
