from sqlmodel import SQLModel, Field, Relationship
from uuid import uuid4, UUID
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from app.modules.questionnaires.models.questionnaire import Questionnaire


def _current_timestamp() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Question(SQLModel, table=True):
    __tablename__ = "questions"

    question_id: UUID = Field(default_factory=uuid4, primary_key=True)
    questionnaire_id: UUID = Field(foreign_key="questionnaires.questionnaire_id", index=True)

    question_text: str = Field(nullable=False)
    order_index: int = Field(default=0)
    is_multiple_choice: bool = Field(default=False)
    is_active: bool = Field(default=True)

    created_at: datetime = Field(default_factory=_current_timestamp)
    updated_at: datetime = Field(default_factory=_current_timestamp)

    # Relationships
    questionnaire: Optional["Questionnaire"] = Relationship(back_populates="questions")
    answers: List["AnswerOption"] = Relationship(
        back_populates="question",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "AnswerOption.order_index",
            "lazy": "selectin",
        }
    )
