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

    def __init__(self):
        self.ai_service_url = getattr(settings, 'AI_SERVICE_URL', "http://localhost:8001")
        self.ai_api_key = getattr(settings, 'AI_API_KEY', "")
        self.ai_timeout = getattr(settings, 'AI_SERVICE_TIMEOUT', 30)
        self.ai_max_retries = getattr(settings, 'AI_MAX_RETRIES', 3)

        self.upload_dir = getattr(settings, 'UPLOAD_DIR', "./uploads")
        self.base_url = getattr(settings, 'BASE_URL', "http://localhost:8000")

        self.min_accuracy_threshold = 0.65

        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.ai_timeout),
            headers={"X-API-Key": self.ai_api_key}
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()

    @classmethod
    def validate_ai_class(cls, wound_type: str, severity: str) -> bool:
        """
        Validate if wound_type and severity combination is valid.
        """
        if wound_type.lower() not in cls.SUPPORTED_WOUND_TYPES:
            logger.warning(f"Invalid wound_type from AI: {wound_type}")
            return False

        if wound_type.lower() == "burn" and "_" in severity:
            base_severity = severity.split("_")[0]  
            if base_severity.lower() not in cls.SUPPORTED_SEVERITIES:
                logger.warning(f"Invalid base severity from AI: {base_severity} (from {severity})")
                return False
        else:
            if severity.lower() not in cls.SUPPORTED_SEVERITIES:
                logger.warning(f"Invalid severity from AI: {severity}")
                return False

        return True

    @classmethod
    def validate_burn_subtype(cls, sub_type: str) -> bool:
        """Validate burn sub-type."""
        if not sub_type:
            return True  
        
        if sub_type.lower() not in cls.SUPPORTED_BURN_SUBTYPES:
            logger.warning(f"Invalid burn sub-type from AI: {sub_type}")
            return False
        
        return True

    async def call_ai_service(self, image_path: str) -> Dict[str, Any]:
        """Gọi đến ai_ml service để phân tích ảnh"""
        try:
            async with aiofiles.open(image_path, 'rb') as f:
                image_data = await f.read()

            endpoint = f"{self.ai_service_url}/analyze/"
            
            logger.info(f"[AI] Calling: {endpoint}")

            response = await self.http_client.post(
                endpoint,
                files={"file": ("image.jpg", image_data, "image/jpeg")}
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
                logger.error(f"[AI] Error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"AI service error: {response.status_code}",
                    "error_code": "AI_SERVICE_ERROR",
                    "total_detections": 0,
                    "detections": []
                }

        except httpx.TimeoutException:
            logger.error("[AI] Timeout")
            return {
                "success": False,
                "error": "AI service timeout",
                "error_code": "AI_SERVICE_TIMEOUT",
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

    async def analyze_wound_image(self, image_path: str) -> Dict[str, Any]:
        """
        Phân tích ảnh vết thương.
        """
        try:
            start_time = cv2.getTickCount()

            # Step 1: Call AI
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

            # Step 2: Parse detections
            raw_detections = ai_result.get("detections", [])
            processing_time_ms = ai_result.get("processing_time_ms", 0)
            processing_time = processing_time_ms / 1000.0

            # Check if primary_wound_type is "normal skin" - if so, ignore all detections
            primary_wound_type = ai_result.get("primary_wound_type", "")
            if primary_wound_type and "normal" in primary_wound_type.lower() and "skin" in primary_wound_type.lower():
                logger.info(f"[ANALYZE] Primary wound type is '{primary_wound_type}', treating as no wound detected")
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

            # Step 3: Process and validate detections
            final_detections = []
            invalid_count = 0
            
            for i, detection in enumerate(raw_detections):
                try:
                    # Parse bbox
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

                    # Get detection info
                    wound_type = detection.get("wound_type", "unknown")
                    severity = detection.get("severity", "unknown")
                    confidence = detection.get("confidence_score", 0.0)
                    
                    # Validate against supported classes
                    if not self.validate_ai_class(wound_type, severity):
                        logger.warning(
                            f"[VALIDATE] Skipping invalid detection: "
                            f"{wound_type}/{severity} (not in supported classes)"
                        )
                        invalid_count += 1
                        continue
                    
                    # Additional validation for burn sub-types
                    if wound_type.lower() == "burn" and "_" in severity:
                        parts = severity.split("_")
                        if len(parts) > 1:
                            sub_type = parts[-1]  # "blister" or "skintear"
                            if not self.validate_burn_subtype(sub_type):
                                logger.warning(
                                    f"[VALIDATE] Invalid burn sub-type: {sub_type}"
                                )
                                invalid_count += 1
                                continue
                    
                    logger.debug(
                        f"[VALIDATE] Detection {i}: {wound_type}/{severity} "
                        f"(confidence: {confidence:.2%})"
                    )

                    final_detection = {
                        "wound_type": wound_type,
                        "confidence": confidence,
                        "bbox": bbox,
                        "bounding_box": bounding_box,
                        "severity": severity,
                        "severity_confidence": confidence,
                        "detection_index": i,
                        "is_primary": False,
                    }

                    final_detections.append(final_detection)

                except Exception as e:
                    logger.error(f"Failed to process detection {i}: {e}", exc_info=True)
                    continue

            # Log validation summary
            if invalid_count > 0:
                logger.warning(
                    f"[VALIDATE] Filtered out {invalid_count} invalid detections "
                    f"(not in supported classes)"
                )

            # Step 4: Filter by confidence threshold
            reliable_detections = [
                d for d in final_detections 
                if d.get("confidence", 0) >= self.min_accuracy_threshold
            ]

            logger.info(
                f"[ANALYZE] Processed: {len(final_detections)} valid detections, "
                f"{len(reliable_detections)} meet threshold (>={self.min_accuracy_threshold:.0%})"
            )

            # Step 5: Build result
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
                f"[ANALYZE] Complete: {result['num_detections']} detections, "
                f"{result['reliable_detections']} reliable, "
                f"avg confidence: {result['average_confidence']:.2%}, "
                f"time: {processing_time:.3f}s"
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
                    "wound_classes": model_info.get("wound_classes", self.VALID_AI_CLASSES),
                    "num_wound_classes": model_info.get("num_wound_classes", len(self.VALID_AI_CLASSES))
                },
                "supported_classes": {
                    "wound_types": self.SUPPORTED_WOUND_TYPES,
                    "severities": self.SUPPORTED_SEVERITIES,
                    "burn_subtypes": self.SUPPORTED_BURN_SUBTYPES,
                    "all_classes": self.VALID_AI_CLASSES
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
                "supported_wound_types": self.SUPPORTED_WOUND_TYPES,
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
                "supported_classes": {
                    "wound_types": self.SUPPORTED_WOUND_TYPES,
                    "severities": self.SUPPORTED_SEVERITIES,
                    "burn_subtypes": self.SUPPORTED_BURN_SUBTYPES,
                    "all_classes": self.VALID_AI_CLASSES
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
                "supported_wound_types": self.SUPPORTED_WOUND_TYPES
            }