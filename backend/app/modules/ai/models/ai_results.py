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

    # "classification" | "detail" | "generation"
    result_type: str = Field(max_length=20)

    model_id: Optional[UUID] = Field(default=None, nullable=True)
    model_name: str = Field(max_length=100)
    model_version: str = Field(max_length=50)

    # classification: {class, confidence, bounding_boxes[], detections[]}
    # detail:         {wound_type, severity, sub_type, confidence, features{}}
    # generation:     {steps[], warnings[], see_doctor, sources{db[], rag[]}}
    results: dict = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))

    confidence_breakdown: Optional[dict] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    processing_time_ms: Optional[int] = Field(default=None)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
