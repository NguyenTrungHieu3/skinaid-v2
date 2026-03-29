from sqlmodel import SQLModel, Field
from sqlalchemy import UUID
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID

class GuideAnalytics(SQLModel, table=True):
    __tablename__ = "guide_analytics"

    analytics_id: UUID = Field(default_factory=uuid4, primary_key=True)
    guide_id: UUID = Field(foreign_key="firstaid_guides.firstaidguide_id", index=True)
    
    total_views: int = Field(default=0, ge=0)
    unique_viewers: int = Field(default=0, ge=0)
    avg_time_spent_seconds: Optional[int] = Field(default=None, ge=0)
    
    helpful_votes: int = Field(default=0, ge=0)
    not_helpful_votes: int = Field(default=0, ge=0)
    
    last_updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
