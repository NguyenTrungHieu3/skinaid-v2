from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID

class AIResult(SQLModel, table=True):
    __tablename__ = "ai_results"

    result_id: UUID = Field(default_factory=uuid4, primary_key=True)
    analysis_id: UUID = Field(foreign_key="analyses.analysis_id", index=True)
    stage: str = Field(max_length=50, index=True)
    
    raw_output: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    processed_output: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    execution_time_ms: Optional[int] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
