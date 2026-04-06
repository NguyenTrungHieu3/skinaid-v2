from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4, UUID
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

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
    is_active: bool = Field(default=False, index=True) # Default is drafting
    
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
