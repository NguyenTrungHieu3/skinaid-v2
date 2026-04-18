from sqlmodel import SQLModel, Field, Relationship
from uuid import uuid4, UUID
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from app.modules.questionnaires.models.question import Question


def _current_timestamp() -> datetime:
    """Generate current UTC timestamp without timezone info."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Questionnaire(SQLModel, table=True):
    __tablename__ = "questionnaires"

    questionnaire_id: UUID = Field(default_factory=uuid4, primary_key=True)
    # unique=True removed: partial unique index enforces only 1 active per wound_type (DB-level)
    wound_type: str = Field(nullable=False, index=True)
    title: str = Field(nullable=False)
    description: Optional[str] = None
    is_active: bool = Field(default=False, index=True)  # Default is drafting

    created_at: datetime = Field(default_factory=_current_timestamp)
    updated_at: datetime = Field(default_factory=_current_timestamp)

    # Relationships
    questions: List["Question"] = Relationship(
        back_populates="questionnaire",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "Question.order_index",
            "lazy": "selectin",
        }
    )
