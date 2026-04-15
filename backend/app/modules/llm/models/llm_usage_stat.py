from sqlmodel import SQLModel, Field
from uuid import uuid4, UUID
from typing import Optional
from datetime import datetime, timezone


class LLMUsageStat(SQLModel, table=True):
    """Per-request usage statistics for LLM calls."""

    __tablename__ = "llm_usage_stats"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    config_key: str = Field(max_length=50, index=True)
    model_name: str = Field(max_length=100)

    tokens_prompt: int = Field(default=0)
    tokens_completion: int = Field(default=0)
    tokens_total: int = Field(default=0)

    response_time_ms: int = Field(default=0)

    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
