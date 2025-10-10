import httpx
from typing import Dict, Any
from pathlib import Path
import logging
import time
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

from app.core.config import settings

AI_SERVICE_URL = getattr(settings, 'AI_SERVICE_URL', "http://localhost:8001")
AI_SERVICE_TIMEOUT = getattr(settings, 'AI_SERVICE_TIMEOUT', 30)
AI_MAX_RETRIES = getattr(settings, 'AI_MAX_RETRIES', 3)

RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.TimeoutException,
    httpx.NetworkError,
)
class AIProcessingService:

    def __init__(self):
        self.ai_service_url = AI_SERVICE_URL
        self.ai_service_timeout = AI_SERVICE_TIMEOUT
        self.ai_max_retries = AI_MAX_RETRIES

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True
    )
    async def _make_request(self, url: str, method: str = "GET", **kwargs) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                return await client.get(url, **kwargs)
            elif method.upper() == "POST":
                return await client.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

    async def check_ai_service_health(self) -> bool:
        try:
            response = await self._make_request(
                f"{self.ai_service_url}/health",
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"
            
            return False
            
        except httpx.ConnectError:
            logger.error("Cannot connect to AI service. Is it running?")
            return False
        except httpx.TimeoutException:
            logger.error("AI service health check timed out")
            return False
        except Exception as e:
            logger.error(f"AI service health check failed: {e}")
            return False
    
    async def analyze_image(
        self,
        image_path: str,
        max_retries: int = None
    ) -> Dict[str, Any]:
        if max_retries is None:
            max_retries = self.ai_max_retries
            
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    if not await self.check_ai_service_health():
                        return {
                            "success": False,
                            "error": "AI service is not available",
                            "error_code": "AI_SERVICE_UNAVAILABLE",
                            "num_detections": 0,
                            "detections": []
                        }
                
                start_time = time.time()
                
                with open(image_path, "rb") as f:
                    ext = Path(image_path).suffix.lower()
                    mime_type = "image/jpeg" if ext in ['.jpg', '.jpeg'] else "image/png"
                    
                    files = {
                        "file": (Path(image_path).name, f, mime_type)
                    }
                    
                    logger.info(
                        f"Sending image to AI service (attempt {attempt + 1}/{max_retries})",
                        extra={"image_path": image_path, "ai_service_url": self.ai_service_url}
                    )
                    
                    response = await self._make_request(
                        f"{self.ai_service_url}/detect",
                        method="POST",
                        files=files,
                        timeout=self.ai_service_timeout
                    )
                    
                    request_time = time.time() - start_time

                    if response.status_code == 200:
                        result = response.json()
                        
                        logger.info(
                            f"AI service returned: {result.get('num_detections', 0)} detections "
                            f"in {request_time:.3f}s",
                            extra={
                                "num_detections": result.get("num_detections", 0),
                                "processing_time": result.get("processing_time", 0),
                                "request_time": request_time
                            }
                        )
                        
                        if "processing_time" not in result:
                            result["processing_time"] = round(request_time, 3)

                        if "success" not in result:
                            result["success"] = True
                        
                        return result
                    
                    else:
                        error_detail = response.text
                        logger.error(
                            f"AI service returned error: {response.status_code}",
                            extra={"status_code": response.status_code, "detail": error_detail}
                        )
                        
                        return {
                            "success": False,
                            "error": f"AI service error: {response.status_code}",
                            "error_code": f"HTTP_{response.status_code}",
                            "num_detections": 0,
                            "detections": []
                        }
            
            except httpx.ConnectError as e:
                last_error = e
                logger.error(
                    f"Cannot connect to AI service (attempt {attempt + 1}/{max_retries})",
                    extra={"error": str(e), "ai_service_url": self.ai_service_url}
                )
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt) 
                    continue
                
            except httpx.TimeoutException as e:
                last_error = e
                logger.error(
                    f"AI service timeout after {self.ai_service_timeout}s (attempt {attempt + 1}/{max_retries})"
                )
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt) 
                    continue
                
            except FileNotFoundError as e:
                logger.error(f"Image file not found: {image_path}")
                return {
                    "success": False,
                    "error": f"Image file not found: {image_path}",
                    "error_code": "FILE_NOT_FOUND",
                    "num_detections": 0,
                    "detections": []
                }
                
            except Exception as e:
                last_error = e
                logger.error(
                    f"Failed to analyze image (attempt {attempt + 1}/{max_retries}): {e}",
                    exc_info=True
                )
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt) 
                    continue
        
        error_message = str(last_error) if last_error else "Unknown error"
        error_code = type(last_error).__name__ if last_error else "UNKNOWN_ERROR"
        
        return {
            "success": False,
            "error": f"AI service request failed: {error_message}",
            "error_code": error_code,
            "num_detections": 0,
            "detections": []
        }
    
    async def get_model_info(self) -> Dict[str, Any]:
        try:
            response = await self._make_request(
                f"{self.ai_service_url}/model-info",
                timeout=5.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}