import os
import cv2
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import logging
import httpx
import aiofiles
from pathlib import Path
import uuid
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

class WoundAIService:

    def __init__(self):
        self.ai_service_url = getattr(settings, 'AI_SERVICE_URL', "http://localhost:8001")
        self.ai_api_key = getattr(settings, 'AI_API_KEY', "")
        self.ai_timeout = getattr(settings, 'AI_SERVICE_TIMEOUT', 30)
        self.ai_max_retries = getattr(settings, 'AI_MAX_RETRIES', 3)

        self.upload_dir = getattr(settings, 'UPLOAD_DIR', "./uploads")
        self.base_url = getattr(settings, 'BASE_URL', "http://localhost:8000")

        self.min_accuracy_threshold = 0.65

        self.supported_wound_types = [
            "scratch", "bruise", "burn", "cut", "wound"
        ]

        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.ai_timeout),
            headers={"X-API-Key": self.ai_api_key}
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()

    def _generate_image_path(self, user_id: str, original_filename: str) -> Tuple[str, str]:
        """Tạo đường dẫn lưu ảnh theo format: uploads/YYYY/MM/DD/user_id_timestamp_uuid.ext"""
        now = datetime.now()
        date_path = now.strftime("%Y/%m/%d")

        timestamp = int(now.timestamp())
        unique_id = str(uuid.uuid4())[:8]

        file_ext = Path(original_filename).suffix.lower()
        if not file_ext:
            file_ext = ".jpg"

        new_filename = f"{user_id}_{timestamp}_{unique_id}{file_ext}"

        full_path = os.path.join(self.upload_dir, date_path, new_filename)

        return full_path, f"{date_path}/{new_filename}"

    async def save_image_locally(self, image_data: bytes, user_id: str, original_filename: str) -> Tuple[str, str]:
        """Lưu ảnh vào thư mục local và trả về đường dẫn file và URL"""

        # Tạo đường dẫn lưu ảnh
        file_path, relative_path = self._generate_image_path(user_id, original_filename)

        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Lưu ảnh vào file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(image_data)

        # Tạo URL để truy cập ảnh
        image_url = f"{self.base_url}/uploads/{relative_path}"

        logger.info(f"Image saved locally: {file_path}")
        return file_path, image_url

    async def call_ai_service(self, image_path: str) -> Dict[str, Any]:
        """Gọi đến ai_ml service để phân tích ảnh"""

        try:
            async with aiofiles.open(image_path, 'rb') as f:
                image_data = await f.read()

            endpoint = f"{self.ai_service_url}/analyze/"  
            
            logger.info(f"Calling AI service at: {endpoint}")

            response = await self.http_client.post(
                endpoint,
                files={"file": ("image.jpg", image_data, "image/jpeg")}
            )

            if response.status_code == 200:
                result = response.json()
                
                logger.info(f"AI service response: {result}")
                logger.info(f"AI service analysis completed: {result.get('total_detections', 0)} detections")
                
                for i, det in enumerate(result.get("detections", [])):
                    logger.info(
                        f"Raw detection {i}: wound_type='{det.get('wound_type')}', "
                        f"severity='{det.get('severity')}', "
                        f"confidence_score={det.get('confidence_score')}"
                    )
                
                return result
            else:
                logger.error(f"AI service error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"AI service error: {response.status_code}",
                    "error_code": "AI_SERVICE_ERROR",
                    "total_detections": 0,
                    "detections": []
                }

        except httpx.TimeoutException:
            logger.error("AI service timeout")
            return {
                "success": False,
                "error": "AI service timeout",
                "error_code": "AI_SERVICE_TIMEOUT",
                "total_detections": 0,
                "detections": []
            }
        except Exception as e:
            logger.error(f"AI service call failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "AI_SERVICE_ERROR",
                "total_detections": 0,
                "detections": []
            }

    async def analyze_wound_image(self, image_path: str) -> Dict[str, Any]:
        """Phân tích ảnh vết thương bằng cách gọi đến ai_ml service"""

        try:
            start_time = cv2.getTickCount()

            ai_result = await self.call_ai_service(image_path)

            if not ai_result.get("success", False):
                processing_time = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
                return {
                    "success": False,
                    "error": ai_result.get("error", "AI service failed"),
                    "error_code": ai_result.get("error_code", "AI_SERVICE_ERROR"),
                    "num_detections": 0,
                    "detections": [],
                    "processing_time": processing_time
                }

            raw_detections = ai_result.get("detections", [])
            processing_time_ms = ai_result.get("processing_time_ms", 0)
            processing_time = processing_time_ms / 1000.0  # Convert to seconds

            if not raw_detections:
                return {
                    "success": True,
                    "num_detections": 0,
                    "detections": [],
                    "processing_time": processing_time,
                    "ai_model_version": ai_result.get("ai_model_version", "YOLOv11_EfficientNetV2_1.0"),
                    "message": "Không phát hiện vết thương nào"
                }

            final_detections = []
            for i, detection in enumerate(raw_detections):
                try:
                    bbox_dict = detection.get("bbox", {})
                    
                    # Handle bbox format from ai_ml: {"x": ..., "y": ..., "width": ..., "height": ...}
                    if isinstance(bbox_dict, dict) and "x" in bbox_dict:
                        x = int(bbox_dict.get("x", 0))
                        y = int(bbox_dict.get("y", 0))
                        width = int(bbox_dict.get("width", 100))
                        height = int(bbox_dict.get("height", 100))
                        
                        bbox = [x, y, x + width, y + height]
                        bounding_box = {
                            "x": x,
                            "y": y,
                            "width": width,
                            "height": height
                        }
                    else:
                        # Fallback for unexpected format
                        bbox = [0, 0, 100, 100]
                        bounding_box = {"x": 0, "y": 0, "width": 100, "height": 100}

                    # Get wound_type and severity directly from ai_ml response
                    wound_type = detection.get("wound_type", "wound")
                    severity = detection.get("severity", "mild")
                    
                    # Get confidence (ai_ml uses "confidence_score")
                    confidence = detection.get("confidence_score", 0.0)
                    
                    logger.info(
                        f"Detection {i}: wound_type='{wound_type}', severity='{severity}', "
                        f"confidence={confidence:.2f}"
                    )

                    final_detection = {
                        "wound_type": wound_type,
                        "confidence": confidence,
                        "bbox": bbox,
                        "bounding_box": bounding_box,
                        "severity": severity,
                        "severity_confidence": confidence,  # ai_ml uses same confidence for both
                        "detection_index": i,
                        "is_primary": False,  
                    }

                    final_detections.append(final_detection)

                except Exception as e:
                    logger.error(f"Failed to process detection {i}: {e}", exc_info=True)
                    continue

            reliable_detections = [
                d for d in final_detections 
                if d.get("confidence", 0) >= self.min_accuracy_threshold
            ]

            logger.info(
                f"Processed {len(final_detections)} detections, "
                f"{len(reliable_detections)} meet threshold (>= {self.min_accuracy_threshold})"
            )

            result = {
                "success": True,
                "num_detections": len(final_detections),
                "reliable_detections": len(reliable_detections),
                "detections": final_detections,
                "processing_time": processing_time,
                "ai_model_version": ai_result.get("ai_model_version", "YOLOv11_EfficientNetV2_1.0"),
                "meets_accuracy_threshold": len(reliable_detections) > 0,
                "average_confidence": sum(d.get("confidence", 0) for d in final_detections) / len(final_detections) if final_detections else 0.0
            }

            logger.info(
                f"AI analysis completed: {result['num_detections']} total detections, "
                f"{result['reliable_detections']} reliable (>={self.min_accuracy_threshold*100}%), "
                f"avg confidence: {result['average_confidence']:.2f}, "
                f"processing time: {processing_time:.3f}s"
            )

            return result

        except Exception as e:
            logger.error(f"AI analysis failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "AI_PROCESSING_ERROR",
                "num_detections": 0,
                "detections": []
            }

    async def check_model_health(self) -> Dict[str, Any]:
        """Kiểm tra trạng thái AI service và models."""
        try:
            response = await self.http_client.get(f"{self.ai_service_url}/health")

            ai_service_healthy = response.status_code == 200
            ai_service_info = response.json() if ai_service_healthy else {}

            model_response = await self.http_client.get(f"{self.ai_service_url}/model-info")
            model_info = model_response.json() if model_response.status_code == 200 else {}

            return {
                "ai_service": {
                    "url": self.ai_service_url,
                    "healthy": ai_service_healthy,
                    "status": ai_service_info.get("status", "unknown"),
                    "response_time": response.elapsed.total_seconds() if ai_service_healthy else None
                },
                "models": {
                    "detection_model": model_info.get("detection_model", "YOLOv11"),
                    "classification_model": model_info.get("classification_model", "EfficientNetV2"),
                    "wound_classes": model_info.get("wound_classes", []),
                    "num_wound_classes": model_info.get("num_wound_classes", 0)
                },
                "configuration": {
                    "ai_service_url": self.ai_service_url,
                    "ai_timeout": self.ai_timeout,
                    "ai_max_retries": self.ai_max_retries,
                    "upload_dir": self.upload_dir,
                    "min_accuracy_threshold": self.min_accuracy_threshold
                },
                "overall_health": ai_service_healthy,
                "min_accuracy_threshold": self.min_accuracy_threshold,
                "supported_wound_types": self.supported_wound_types,
                "storage": {
                    "type": "local",
                    "upload_dir": self.upload_dir,
                    "base_url": self.base_url
                }
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "ai_service": {
                    "url": self.ai_service_url,
                    "healthy": False,
                    "error": str(e)
                },
                "models": {
                    "detection_model": "YOLOv11",
                    "classification_model": "EfficientNetV2"
                },
                "configuration": {
                    "ai_service_url": self.ai_service_url,
                    "ai_timeout": self.ai_timeout,
                    "ai_max_retries": self.ai_max_retries,
                    "upload_dir": self.upload_dir,
                    "min_accuracy_threshold": self.min_accuracy_threshold
                },
                "overall_health": False,
                "min_accuracy_threshold": self.min_accuracy_threshold,
                "supported_wound_types": self.supported_wound_types
            }