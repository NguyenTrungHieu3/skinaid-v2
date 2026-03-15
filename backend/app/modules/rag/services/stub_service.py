import time
from typing import List, Dict, Any, Optional
import logging

from app.modules.rag.schemas.rag_schemas import (
    RAGRetrieveResponse,
    KnowledgeChunk,
)

logger = logging.getLogger(__name__)


class RAGStubService:
    """
    Stub service for RAG knowledge retrieval (PBI-24).
    
    Returns mock responses until real RAG system is implemented.
    """
    
    def __init__(self):
        self.source = "knowledge_base"
    
    async def retrieve(
        self, 
        query: str, 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> RAGRetrieveResponse:
        """
        Return stub RAG response.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional filters
            
        Returns:
            RAGRetrieveResponse with empty chunks (stub)
        """
        start_time = time.time()
        
        logger.info(f"[RAG STUB] Query: {query}, top_k: {top_k}")
        
        # Return empty chunks for now
        chunks: List[KnowledgeChunk] = []
        
        query_time_ms = int((time.time() - start_time) * 1000)
        
        return RAGRetrieveResponse(
            chunks=chunks,
            source=self.source,
            total_found=0,
            query_time_ms=query_time_ms,
        )
