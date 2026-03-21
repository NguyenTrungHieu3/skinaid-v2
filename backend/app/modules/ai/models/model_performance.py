from sqlmodel import SQLModel, Field
from sqlalchemy import UUID
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID

class ModelPerformance(SQLModel, table=True):
    __tablename__ = "model_performance"

    record_id: UUID = Field(default_factory=uuid4, primary_key=True)
    model_id: UUID = Field(foreign_key="ai_models.model_id", index=True)
    analysis_id: Optional[UUID] = Field(default=None, foreign_key="analyses.analysis_id", index=True)
    
    processing_time_ms: int = Field(ge=0)
    memory_used_mb: Optional[float] = None
    cpu_utilization: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
