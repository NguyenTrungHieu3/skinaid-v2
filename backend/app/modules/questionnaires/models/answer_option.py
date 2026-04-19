from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4, UUID
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from app.modules.questionnaires.models.question import Question


def _current_timestamp() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AnswerOption(SQLModel, table=True):
    __tablename__ = "answer_options"

    answer_id: UUID = Field(default_factory=uuid4, primary_key=True)
    question_id: UUID = Field(foreign_key="questions.question_id", index=True)

    answer_text: str = Field(nullable=False)
    triage_level: str = Field(nullable=False, description="green, yellow, red")
    icon_or_color: Optional[str] = None
    order_index: int = Field(default=0)

    metadata_tags: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    created_at: datetime = Field(default_factory=_current_timestamp)
    updated_at: datetime = Field(default_factory=_current_timestamp)

    # Relationships
    question: Optional["Question"] = Relationship(back_populates="answers")
