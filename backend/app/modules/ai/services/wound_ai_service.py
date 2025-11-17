import os
import cv2
import numpy as np
from typing import Dict, Any
import logging
import aiofiles
from app.core.config import settings
from app.core.clients.http_client import HTTPClient

logger = logging.getLogger(__name__)


class WoundAIService:
    
    SUPPORTED_WOUND_TYPES = ["abrasion", "bruise", "burn"]
    SUPPORTED_SEVERITIES = ["mild", "moderate"]
    SUPPORTED_BURN_SUBTYPES = ["blister", "skintear"]
    VALID_AI_CLASSES = [
        "abrasion_mild",
        "abrasion_moderate",
        "bruise_mild",
        "bruise_moderate",
        "burn_mild",
        "burn_moderate_blister",
        "burn_moderate_skintear"
    ]

    @staticmethod
    def parse_wound_classification(classification: str) -> Dict[str, Any]:
        """
        Phân tích chuỗi phân loại thành các thành phần: wound_type, severity, sub_type.
        
        Cấu trúc: <wound_type>_<severity>_<sub_type1>_<sub_type2>_...
        
        Ví dụ:
            - "burn_moderate_blister" -> {wound_type: "burn", severity: "moderate", sub_type: "blister"}
            - "abrasion_mild" -> {wound_type: "abrasion", severity: "mild", sub_type: None}
            - "burn_severe_skintear_infection" -> {wound_type: "burn", severity: "severe", sub_type: "skintear_infection"}
        
        Args:
            classification: Chuỗi phân loại từ AI (ví dụ: "burn_moderate_blister")
            
        Returns:
            Dict chứa wound_type, severity, sub_type (hoặc None nếu không có)
        """
        parts = classification.split("_")
        
        if len(parts) < 2:
            logger.warning(f"[PARSE] Invalid classification format: {classification}")
            return {
                "wound_type": classification,
                "severity": "unknown",
                "sub_type": None
            }
        
        # Phần đầu tiên luôn là wound_type
        wound_type = parts[0]
        
        # Phần thứ hai luôn là severity
        severity = parts[1]
        
        # Các phần còn lại (nếu có) là sub_type, nối lại bằng dấu gạch dưới
        sub_type = "_".join(parts[2:]) if len(parts) > 2 else None
        
        logger.debug(
            f"[PARSE] '{classification}' -> "
            f"type={wound_type}, severity={severity}, sub_type={sub_type}"
        )
        
        return {
            "wound_type": wound_type,
            "severity": severity,
            "sub_type": sub_type
        }

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
        """
        if wound_type.lower() not in cls.SUPPORTED_WOUND_TYPES:
            logger.warning(f"wound_type không hợp lệ từ AI: {wound_type}")
            return False

        if wound_type.lower() == "burn" and "_" in severity:
            base_severity = severity.split("_")[0]  
            if base_severity.lower() not in cls.SUPPORTED_SEVERITIES:
                logger.warning(f"Mức độ nghiêm trọng cơ bản không hợp lệ từ AI: {base_severity} (từ {severity})")
                return False
        else:
            if severity.lower() not in cls.SUPPORTED_SEVERITIES:
                logger.warning(f"Mức độ nghiêm trọng không hợp lệ từ AI: {severity}")
                return False

        return True

    @classmethod
    def validate_burn_subtype(cls, sub_type: str) -> bool:
        """Xác thực loại bỏng phụ."""
        if not sub_type:
            return True  
        
        if sub_type.lower() not in cls.SUPPORTED_BURN_SUBTYPES:
            logger.warning(f"Loại bỏng phụ không hợp lệ từ AI: {sub_type}")
            return False
        
        return True

    async def call_ai_service(self, image_path: str) -> Dict[str, Any]:
        """Gọi đến ai_ml service để phân tích ảnh"""
        try:
            async with aiofiles.open(image_path, 'rb') as f:
                image_data = await f.read()

            endpoint = f"{self.ai_service_url}/analyze/"
            
            logger.info(f"[AI] Calling: {endpoint}")

            # Prepare headers with API key if available
            headers = {}
            if self.ai_api_key:
                headers["X-API-Key"] = self.ai_api_key

            # Use shared HTTP client for the request
            response = await HTTPClient.post_with_retry(
                url=endpoint,
                files={"file": ("image.jpg", image_data, "image/jpeg")},
                headers=headers,
                timeout=self.ai_timeout
            )

            if response.status_code == 200:
                result = response.json()
                
                logger.info(
                    f"[AI] Response: {result.get('total_detections', 0)} detections, "
                    f"model: {result.get('ai_model_version', 'unknown')}"
                )
                
                for i, det in enumerate(result.get("detections", [])):
                    wound_type = det.get('wound_type', 'unknown')
                    severity = det.get('severity', 'unknown')
                    confidence = det.get('confidence_score', 0)
                    
                    # Validate class
                    is_valid = self.validate_ai_class(wound_type, severity)
                    validation_status = "VALID" if is_valid else "⚠️ INVALID"
                    
                    logger.info(
                        f"  [{i}] {validation_status} - {wound_type}/{severity} "
                        f"(confidence: {confidence:.2%})"
                    )
                
                return result
            else:
                logger.error(f"[AI] Lỗi: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Lỗi dịch vụ AI: {response.status_code}",
                    "error_code": "AI_SERVICE_ERROR",
                    "total_detections": 0,
                    "detections": []
                }

        except Exception as e:
            logger.error(f"[AI] Failed: {e}", exc_info=True)
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

            # Bước 1: Gọi AI
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

            # Bước 2: Phân tích detections
            raw_detections = ai_result.get("detections", [])
            processing_time_ms = ai_result.get("processing_time_ms", 0)
            processing_time = processing_time_ms / 1000.0

            # Kiểm tra nếu primary_wound_type là "normal skin" - nếu vậy, bỏ qua tất cả detections
            primary_wound_type = ai_result.get("primary_wound_type", "")
            if primary_wound_type and "normal" in primary_wound_type.lower() and "skin" in primary_wound_type.lower():
                logger.info(f"[ANALYZE] Loại vết thương chính là '{primary_wound_type}', coi như không phát hiện vết thương")
                return {
                    "success": True,
                    "num_detections": 0,
                    "detections": [],
                    "processing_time": processing_time,
                    "ai_model_version": ai_result.get("ai_model_version", "YOLOv11_EfficientNetV2_1.0"),
                    "message": "Không phát hiện vết thương nào - ảnh chứa da bình thường"
                }

            if not raw_detections:
                return {
                    "success": True,
                    "num_detections": 0,
                    "detections": [],
                    "processing_time": processing_time,
                    "ai_model_version": ai_result.get("ai_model_version", "YOLOv11_EfficientNetV2_1.0"),
                    "message": "Không phát hiện vết thương nào"
                }

            # Bước 3: Xử lý và xác thực detections
            final_detections = []
            invalid_count = 0
            
            for i, detection in enumerate(raw_detections):
                try:
                    # Phân tích bbox
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

                    # Lấy thông tin detection gốc
                    raw_wound_type = detection.get("wound_type", "unknown")
                    raw_severity = detection.get("severity", "unknown")
                    confidence = detection.get("confidence_score", 0.0)
                    
                    # Parse classification để tách wound_type, severity, sub_type
                    # Nếu severity chứa dấu "_", có thể là format cũ: "moderate_blister"
                    if "_" in raw_severity:
                        # Format cũ: wound_type="burn", severity="moderate_blister"
                        # Tạo lại classification đầy đủ
                        full_classification = f"{raw_wound_type}_{raw_severity}"
                    else:
                        # Format chuẩn: wound_type="burn", severity="moderate"
                        full_classification = f"{raw_wound_type}_{raw_severity}"
                    
                    parsed = self.parse_wound_classification(full_classification)
                    wound_type = parsed["wound_type"]
                    severity = parsed["severity"]
                    sub_type = parsed["sub_type"]
                    
                    # Xác thực với các lớp được hỗ trợ
                    if not self.validate_ai_class(wound_type, severity):
                        logger.warning(
                            f"[VALIDATE] Bỏ qua detection không hợp lệ: "
                            f"{wound_type}/{severity} (không trong các lớp được hỗ trợ)"
                        )
                        invalid_count += 1
                        continue
                    
                    # Xác thực bổ sung cho sub_type (nếu có)
                    if sub_type and wound_type.lower() == "burn":
                        # Lấy sub_type đầu tiên nếu có nhiều (ví dụ: "skintear_infection" -> "skintear")
                        primary_subtype = sub_type.split("_")[0]
                        if not self.validate_burn_subtype(primary_subtype):
                            logger.warning(
                                f"[VALIDATE] Loại bỏng phụ không hợp lệ: {primary_subtype}"
                            )
                            invalid_count += 1
                            continue
                    
                    logger.debug(
                        f"[VALIDATE] Detection {i}: {wound_type}/{severity}"
                        f"{f'/{sub_type}' if sub_type else ''} "
                        f"(confidence: {confidence:.2%})"
                    )

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

                except Exception as e:
                    logger.error(f"Failed to process detection {i}: {e}", exc_info=True)
                    continue

            # Ghi log tóm tắt xác thực
            if invalid_count > 0:
                logger.warning(
                    f"[VALIDATE] Đã lọc ra {invalid_count} detections không hợp lệ "
                    f"(không trong các lớp được hỗ trợ)"
                )

            # Bước 4: Lọc theo ngưỡng confidence
            reliable_detections = [
                d for d in final_detections 
                if d.get("confidence", 0) >= self.min_accuracy_threshold
            ]

            logger.info(
                f"[ANALYZE] Đã xử lý: {len(final_detections)} detections hợp lệ, "
                f"{len(reliable_detections)} đạt ngưỡng (>={self.min_accuracy_threshold:.0%})"
            )

            # Bước 5: Xây dựng kết quả
            result = {
                "success": True,
                "num_detections": len(final_detections),
                "reliable_detections": len(reliable_detections),
                "detections": final_detections,
                "processing_time": processing_time,
                "ai_model_version": ai_result.get("ai_model_version", "YOLOv11_EfficientNetV2_1.0"),
                "meets_accuracy_threshold": len(reliable_detections) > 0,
                "average_confidence": (
                    sum(d.get("confidence", 0) for d in final_detections) / len(final_detections)
                    if final_detections else 0.0
                )
            }

            logger.info(
                f"[ANALYZE] Hoàn thành: {result['num_detections']} detections, "
                f"{result['reliable_detections']} đáng tin cậy, "
                f"confidence trung bình: {result['average_confidence']:.2%}, "
                f"thời gian: {processing_time:.3f}s"
            )

            return result

        except Exception as e:
            logger.error(f"[ANALYZE] Failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "AI_PROCESSING_ERROR",
                "num_detections": 0,
                "detections": []
            }

    async def check_model_health(self) -> Dict[str, Any]:
        """Simple health check for AI service."""
        try:
            # Prepare headers with API key if available
            headers = {}
            if self.ai_api_key:
                headers["X-API-Key"] = self.ai_api_key
            
            # Use shared HTTP client for health check
            response = await HTTPClient.get_with_retry(
                f"{self.ai_service_url}/health",
                headers=headers,
                timeout=10.0  # Shorter timeout for health check
            )
            healthy = response.status_code == 200

            return {
                "overall_health": healthy,
                "status": "healthy" if healthy else "unhealthy"
            }

        except Exception as e:
            logger.error(f"AI health check failed: {e}")
            return {
                "overall_health": False,
                "status": "unhealthy"
            }