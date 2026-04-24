from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime
from typing import Optional
import uuid
from datetime import datetime, timezone

class UserQuestionnaireResponse(SQLModel, table=True):
    __tablename__ = "user_questionnaire_responses"

    response_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    analysis_id: uuid.UUID = Field(foreign_key="analyses.analysis_id", index=True)
    question_id: uuid.UUID = Field(foreign_key="questions.question_id", index=True)
    answer_id: uuid.UUID = Field(foreign_key="answer_options.answer_id")

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    def __repr__(self) -> str:
        return f"<UserQuestionnaireResponse(analysis={self.analysis_id}, q={self.question_id}, a={self.answer_id})>"
