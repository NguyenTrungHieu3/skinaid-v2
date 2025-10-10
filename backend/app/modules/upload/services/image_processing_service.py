import httpx
from typing import Dict, Any, Optional
import logging
import time
import asyncio
import os
from app.core.config import settings
from app.utils.constants.error_codes import *

logger = logging.getLogger(__name__)

class ImageProcessingService:
    """
    ImageProcessingService - AI INTEGRATION SPECIALIST

    Trách nhiệm DUY NHẤT: Giao tiếp với AI service
    - Gọi AI service để phân tích ảnh
    - Xử lý response từ AI service
    - Retry logic và error handling
    - Health check cho AI service

    """

    def __init__(self):
        self.ai_service_url = getattr(settings, 'AI_SERVICE_URL', "http://localhost:8001")
        self.ai_service_timeout = getattr(settings, 'AI_SERVICE_TIMEOUT', 30)
        self.max_retries = getattr(settings, 'AI_MAX_RETRIES', 1)

    async def check_ai_service_health(self) -> bool:
        """
        Kiểm tra AI service có hoạt động không

        Returns:
            bool: True nếu service healthy
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ai_service_url}/health",
                    timeout=5.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("status") == "healthy"

                return False

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.error(f"Kiểm tra trạng thái AI service thất bại: {e}")
            return False
        except Exception as e:
            logger.error(f"Lỗi không mong muốn trong quá trình kiểm tra trạng thái: {e}")
            return False

    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Gửi ảnh tới AI service để phân tích

        Args:
            image_path: Đường dẫn tuyệt đối tới file ảnh

        Returns:
            Dict chứa kết quả từ AI service hoặc error
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                if attempt == 0:
                    if not await self.check_ai_service_health():
                        return {
                            "success": False,
                            "error": "AI service không khả dụng",
                            "error_code": "AI_SERVICE_UNAVAILABLE",
                            "num_detections": 0,
                            "detections": []
                        }

                start_time = time.time()

                async with httpx.AsyncClient() as client:
                    with open(image_path, "rb") as f:
                        ext = image_path.split('.')[-1].lower()
                        mime_type = "image/jpeg" if ext in ['jpg', 'jpeg'] else "image/png"

                        files = {
                            "file": (os.path.basename(image_path), f, mime_type)
                        }

                        logger.info(f"Đang gửi hình ảnh tới AI service (lần thử {attempt + 1})")

                        response = await client.post(
                            f"{self.ai_service_url}/detect",
                            files=files,
                            timeout=self.ai_service_timeout
                        )

                        request_time = time.time() - start_time

                        if response.status_code == 200:
                            result = response.json()

                            logger.info(
                                f"Phân tích AI thành công: {result.get('num_detections', 0)} phát hiện "
                                f"trong {request_time:.3f}s"
                            )

                            return result

                        else:
                            error_detail = response.text
                            logger.error(f"Lỗi HTTP từ AI service: {response.status_code}")

                            return {
                                "success": False,
                                "error": f"AI service error: {response.status_code}",
                                "error_code": f"HTTP_{response.status_code}",
                                "num_detections": 0,
                                "detections": []
                            }

            except httpx.ConnectError as e:
                last_error = e
                logger.error(f"Không thể kết nối tới AI service (lần thử {attempt + 1})")

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                    continue

            except httpx.TimeoutException as e:
                last_error = e
                logger.error(f"AI service timeout after {self.ai_service_timeout}s")

                if attempt < self.max_retries - 1:
                    continue

            except FileNotFoundError as e:
                logger.error(f"Không tìm thấy file hình ảnh: {image_path}")
                return {
                    "success": False,
                    "error": f"Không tìm thấy file hình ảnh: {image_path}",
                    "error_code": "FILE_NOT_FOUND",
                    "num_detections": 0,
                    "detections": []
                }

            except Exception as e:
                last_error = e
                logger.error(f"Lỗi không mong muốn trong quá trình phân tích AI (lần thử {attempt + 1}): {e}")

                if attempt < self.max_retries - 1:
                    continue

        error_message = str(last_error) if last_error else "Lỗi không xác định"
        error_code = type(last_error).__name__ if last_error else "UNKNOWN_ERROR"

        return {
            "success": False,
            "error": f"Yêu cầu AI service thất bại: {error_message}",
            "error_code": error_code,
            "num_detections": 0,
            "detections": []
        }

    async def get_model_info(self) -> Dict[str, Any]:
        """
        Lấy thông tin model từ AI service (debug/monitoring)

        Returns:
            Dict chứa model metadata hoặc error
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ai_service_url}/model-info",
                    timeout=5.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"Không thể lấy thông tin model: {e}")
            return {"error": str(e)}