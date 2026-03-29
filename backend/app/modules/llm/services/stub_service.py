import time
from typing import Optional, Dict, Any
import logging

from app.modules.llm.schemas.llm_schemas import (
    LLMSynthesizeResponse,
)

logger = logging.getLogger(__name__)


class LLMStubService:
    """
    Stub service for LLM response synthesis (PBI-25).
    
    Returns mock responses until real LLM is implemented.
    """
    
    def __init__(self):
        self.default_guidance = "Đang phát triển... Tính năng này sẽ cung cấp hướng dẫn chi tiết dựa trên phân tích AI và cơ sở tri thức y khoa."
    
    async def synthesize(
        self,
        query: str,
        context: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> LLMSynthesizeResponse:
        """
        Return stub LLM response.
        
        Args:
            query: User query
            context: Optional context from RAG
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: Optional system prompt
            
        Returns:
            LLMSynthesizeResponse with placeholder guidance
        """
        start_time = time.time()
        
        logger.info(f"[LLM STUB] Query: {query}, context: {context}")
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return LLMSynthesizeResponse(
            guidance=self.default_guidance,
            validated=False,
            model_version=None,
            tokens_used=0,
            processing_time_ms=processing_time_ms,
            confidence_score=None,
        )
