from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class LLMSynthesizeRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="User query for synthesis")
    context: Optional[str] = Field(None, description="Optional context from RAG retrieval")
    max_tokens: int = Field(default=500, ge=50, le=2000, description="Maximum tokens in response")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt for LLM")


class LLMSynthesizeResponse(BaseModel):
    guidance: str = Field(..., description="LLM-generated guidance/response")
    validated: bool = Field(False, description="Whether the response has been validated")
    model_version: Optional[str] = Field(None, description="Version of the LLM model used")
    tokens_used: int = Field(0, description="Number of tokens used in generation")
    processing_time_ms: int = Field(0, description="Processing time in milliseconds")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")
