from sqlmodel import SQLModel, Field
from sqlalchemy import UUID
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID

class UserInput(SQLModel, table=True):
    __tablename__ = "user_inputs"

    input_id: UUID = Field(default_factory=uuid4, primary_key=True)
    analysis_id: UUID = Field(foreign_key="analyses.analysis_id", index=True)
    
    question_key: str = Field(max_length=100)
    question_text: str
    answer_value: Optional[str] = None
    
    asked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    answered_at: Optional[datetime] = None
