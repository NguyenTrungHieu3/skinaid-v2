from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
import uuid
from typing import Optional

class FirstAidGuide(SQLModel, table=True):
    __tablename__ = "firstaidguides"
    
    firstaidguides_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    
    wound_type: str = Field(max_length=100, nullable=False)
    severity: str = Field(nullable=False)  # mild/moderate/severe
    
    cause: Optional[str] = None
    symptoms: Optional[str] = None
    risks: Optional[str] = None
    first_aid_do: Optional[str] = None
    first_aid_dont: Optional[str] = None
    tip_easy_remember: Optional[str] = None
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )