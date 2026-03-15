from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ModelInfo(BaseModel):
    model_id: UUID = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    type: str = Field(..., description="Model type: wound_detection, severity_classification, chatbot, rag, llm")
    status: str = Field(..., description="Model status: active, inactive, deprecated")
    created_at: datetime = Field(..., description="Model creation timestamp")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Optional performance metrics")


class ModelListResponse(BaseModel):
    models: List[ModelInfo] = Field(default_factory=list, description="List of all models")
    active_version: Optional[str] = Field(None, description="Currently active version")
    total: int = Field(0, description="Total number of models")


class ModelActivateRequest(BaseModel):
    force: bool = Field(False, description="Force activate even if validation fails")


class ModelActivateResponse(BaseModel):
    success: bool = Field(..., description="Whether activation was successful")
    active_version: str = Field(..., description="Newly activated version")
    previous_version: Optional[str] = Field(None, description="Previously active version")
    activated_at: datetime = Field(default_factory=datetime.utcnow, description="Activation timestamp")
