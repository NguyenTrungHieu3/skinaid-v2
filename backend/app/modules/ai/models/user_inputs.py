from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Any
from datetime import datetime, timezone
from uuid import uuid4, UUID


class UserInput(SQLModel, table=True):
    __tablename__ = "user_inputs"

    input_id: UUID = Field(default_factory=uuid4, primary_key=True)
    analysis_id: UUID = Field(foreign_key="analyses.analysis_id", index=True)

    # question_template_id intentionally removed — table question_templates does not exist in schema
    question_text: Optional[str] = Field(default=None)
    # text | multiple_choice | scale | boolean
    question_type: Optional[str] = Field(default=None, max_length=50)
    answer: dict = Field(sa_column=Column(JSONB, nullable=False))

    # pending | passed | rejected | expired
    validation_status: str = Field(default="pending", max_length=20, index=True)
    validation_notes: Optional[str] = Field(default=None)
    validated_at: Optional[datetime] = Field(default=None)
    validated_by: Optional[UUID] = Field(default=None, foreign_key="users.user_id")

    used_in_prompt: bool = Field(default=False)
    importance_score: Optional[float] = Field(default=None)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
