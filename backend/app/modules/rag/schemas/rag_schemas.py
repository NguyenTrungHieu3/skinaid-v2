from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class RAGRetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Search query for knowledge retrieval")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top results to return")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters for refinement")


class KnowledgeChunk(BaseModel):
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    content: str = Field(..., description="Chunk content")
    source: str = Field(..., description="Source of the knowledge chunk")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RAGRetrieveResponse(BaseModel):
    chunks: List[KnowledgeChunk] = Field(default_factory=list, description="List of retrieved knowledge chunks")
    source: str = Field("knowledge_base", description="Source of the knowledge")
    total_found: int = Field(0, description="Total number of chunks found")
    query_time_ms: int = Field(0, description="Query execution time in milliseconds")
