import os
import cv2
import numpy as np
from typing import Dict, Any
import aiofiles
from app.core.config import settings
from app.core.clients.http_client import HTTPClient
from app.modules.ai.utils.wound_parser import WoundParser
from app.modules.ai.constants import WoundConstants


class WoundAIService:



    def __init__(self):
        self.ai_service_url = getattr(settings, 'AI_SERVICE_URL', "http://localhost:8001")
        self.ai_api_key = getattr(settings, 'AI_API_KEY', "")
        self.ai_timeout = getattr(settings, 'AI_SERVICE_TIMEOUT', 30)
        self.ai_max_retries = getattr(settings, 'AI_MAX_RETRIES', 3)

        self.upload_dir = getattr(settings, 'UPLOAD_DIR', "./uploads")
        self.base_url = getattr(settings, 'BASE_URL', "http://localhost:8000")

        self.min_accuracy_threshold = 0.65

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @classmethod
    def validate_ai_class(cls, wound_type: str, severity: str) -> bool:
        """
        Xác thực xem sự kết hợp wound_type và severity có hợp lệ không.
        Dermatological types (acne, fungal, psoriasis) only require a valid severity.
        """
        wt = wound_type.lower()
        if wt not in WoundConstants.WOUND_TYPES:
            return False

        if wt == "burn" and "_" in severity:
            base_severity = severity.split("_")[0]
            if base_severity.lower() not in WoundConstants.SEVERITIES:
                return False
        else:
            if severity.lower() not in WoundConstants.SEVERITIES:
                return False

        return True

    @classmethod
    def validate_burn_subtype(cls, sub_type: str) -> bool:
        """Xác thực loại bỏng phụ."""
        if not sub_type:
            return True

        if sub_type.lower() not in WoundConstants.BURN_SUBTYPES:
            return False

        return True

    async def call_ai_service(self, image_path: str) -> Dict[str, Any]:
        """Gọi đến ai_ml service để phân tích ảnh"""
        try:
            async with aiofiles.open(image_path, 'rb') as f:
                image_data = await f.read()

            endpoint = f"{self.ai_service_url}/analyze/"

            headers = {}
            if self.ai_api_key:
                headers["X-API-Key"] = self.ai_api_key

            response = await HTTPClient.post_with_retry(
                url=endpoint,
                files={"file": ("image.jpg", image_data, "image/jpeg")},
                headers=headers,
                timeout=self.ai_timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"AI service error: {response.status_code}",
                    "error_code": "AI_SERVICE_ERROR",
                    "total_detections": 0,
                    "detections": []
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": "AI_SERVICE_ERROR",
                "total_detections": 0,
                "detections": []
            }

    async def analyze_wound(self, image_path: str) -> Dict[str, Any]:
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
            processing_time = processing_time_ms / 1000.0

            primary_wound_type = ai_result.get("primary_wound_type", "")
            if primary_wound_type and "normal" in primary_wound_type.lower() and "skin" in primary_wound_type.lower():
                return {
                    "success": True,
                    "num_detections": 0,
                    "detections": [],
                    "processing_time": processing_time,
                    "processing_time_ms": max(1, processing_time_ms),
                    "ai_model_version": ai_result.get("ai_model_version", "YOLOv11_EfficientNetV2_1.0"),
                    "message": "Không phát hiện vết thương nào - ảnh chứa da bình thường"
                }

            if not raw_detections:
                return {
                    "success": True,
                    "num_detections": 0,
                    "detections": [],
                    "processing_time": processing_time,
                    "processing_time_ms": max(1, processing_time_ms),  
                    "ai_model_version": ai_result.get("ai_model_version", "YOLOv11_EfficientNetV2_1.0"),
                    "message": "Không phát hiện vết thương nào"
                }

            final_detections = []
            invalid_count = 0
            
            for i, detection in enumerate(raw_detections):
                try:
                    bbox_dict = detection.get("bbox", {})
                    
                    if isinstance(bbox_dict, dict) and "x" in bbox_dict:
                        x = int(bbox_dict.get("x", 0))
                        y = int(bbox_dict.get("y", 0))
                        width = int(bbox_dict.get("width", 100))
                        height = int(bbox_dict.get("height", 100))
                        
                        bbox = [x, y, x + width, y + height]
                        bounding_box = {"x": x, "y": y, "width": width, "height": height}
                    else:
                        bbox = [0, 0, 100, 100]
                        bounding_box = {"x": 0, "y": 0, "width": 100, "height": 100}

                    raw_wound_type = detection.get("wound_type", "unknown")
                    raw_severity = detection.get("severity", "unknown")
                    confidence = detection.get("confidence_score", 0.0)
                    
                    if "_" in raw_severity:
                        full_classification = f"{raw_wound_type}_{raw_severity}"
                    else:
                        full_classification = f"{raw_wound_type}_{raw_severity}"
                    
                    parsed = WoundParser.parse_classification(full_classification)
                    wound_type = parsed["wound_type"]
                    severity = parsed["severity"]
                    sub_type = parsed["sub_type"]
                    
                    if not self.validate_ai_class(wound_type, severity):
                        invalid_count += 1
                        continue

                    if sub_type and wound_type.lower() == "burn":
                        primary_subtype = sub_type.split("_")[0]
                        if not self.validate_burn_subtype(primary_subtype):
                            invalid_count += 1
                            continue

                    final_detection = {
                        "wound_type": wound_type,
                        "confidence": confidence,
                        "bbox": bbox,
                        "bounding_box": bounding_box,
                        "severity": severity,
                        "sub_type": sub_type,
                        "severity_confidence": confidence,
                        "detection_index": i,
                        "is_primary": False,
                    }

                    final_detections.append(final_detection)

                except Exception:
                    continue

            reliable_detections = [
                d for d in final_detections
                if d.get("confidence", 0) >= self.min_accuracy_threshold
            ]

            result = {
                "success": True,
                "num_detections": len(final_detections),
                "reliable_detections": len(reliable_detections),
                "detections": final_detections,
                "processing_time": processing_time,
                "processing_time_ms": max(1, processing_time_ms),
                "ai_model_version": ai_result.get("ai_model_version", "YOLOv11_EfficientNetV2_1.0"),
                "meets_accuracy_threshold": len(reliable_detections) > 0,
                "average_confidence": (
                    sum(d.get("confidence", 0) for d in final_detections) / len(final_detections)
                    if final_detections else 0.0
                )
            }

            return result

        except Exception:
            return {
                "success": False,
                "error": "AI processing failed",
                "error_code": "AI_PROCESSING_ERROR",
                "num_detections": 0,
                "detections": []
            }

    async def check_model_health(self) -> Dict[str, Any]:
        try:
            headers = {}
            if self.ai_api_key:
                headers["X-API-Key"] = self.ai_api_key

            response = await HTTPClient.get_with_retry(
                f"{self.ai_service_url}/health",
                headers=headers,
                timeout=10.0
            )
            healthy = response.status_code == 200

            return {
                "overall_health": healthy,
                "status": "healthy" if healthy else "unhealthy"
            }

        except Exception:
            return {
                "overall_health": False,
                "status": "unhealthy"
            }