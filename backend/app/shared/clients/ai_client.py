from typing import Dict, Any
from app.core.clients.http_client import HTTPClient
from app.core.config import settings
import httpx
import logging

logger = logging.getLogger(__name__)

class AIServiceClient:
    """Client wrapper cho AI service"""
    
    def __init__(self):
        self.ai_url = settings.AI_SERVICE_URL
    
    async def detect_wound(
        self,
        image_bytes: bytes,
        filename: str,
        mime_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Gọi AI service để detect wound
        Business-level method với error handling
        """
        client = await HTTPClient.get_client()
        
        files = {
            "file": (filename, image_bytes, mime_type)
        }
        
        try:
            response = await client.post(
                f"{self.ai_url}/detect",
                files=files,
                timeout=30.0
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"AI service error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"AI service request failed: {str(e)}")
            raise