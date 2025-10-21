from typing import List, Dict, Any
from app.modules.ai.schemas.wound_analysis_schemas import (
    WoundAnalysisResponse,
    WoundDetectionSummary
)
from app.modules.ai.services.detection_processor import DetectionProcessor
import logging

logger = logging.getLogger(__name__)


class ResponseMapper:
    @staticmethod
    def to_wound_analysis_response(
        analysis,
        significant_detections: List[Dict[str, Any]]
    ) -> WoundAnalysisResponse:
        """
        Map WoundAnalysis entity sang WoundAnalysisResponse DTO.
        """
        avg_confidence = (
            sum(d.get("confidence", 0.0) for d in significant_detections) /
            len(significant_detections)
            if significant_detections else 0.0
        )

        significant_wounds = []
        for detection in significant_detections:
            det_wound_type = detection.get("wound_type", "unknown")

            # Map wound type
            mapped_wound_type = DetectionProcessor.map_wound_type_for_database(
                det_wound_type
            )

            # Parse severity
            parsed_severity = DetectionProcessor.get_parsed_severity_for_storage(
                det_wound_type,
                detection.get("severity", "mild")
            )

            # Create summary
            wound_summary = WoundDetectionSummary(
                wound_type=mapped_wound_type,
                severity=parsed_severity,
                confidence_score=detection.get("confidence", 0.0),
                bounding_box=detection.get("bounding_box", {}),
                is_primary=detection.get("is_primary", False)
            )
            significant_wounds.append(wound_summary)

        # Build response data (avoid accessing lazy-loaded properties)
        response_data = {
            "analysis_id": analysis.analysis_id,
            "user_id": analysis.user_id,
            "image_url": analysis.image_url,
            "file_name": analysis.file_name,
            "file_size": analysis.file_size,
            "ai_model_version": analysis.ai_model_version,
            "total_detections": analysis.total_detections,
            "processing_time_ms": analysis.processing_time_ms,
            "processing_time_seconds": round(analysis.processing_time_ms / 1000, 3) if analysis.processing_time_ms > 0 else None,
            "primary_wound_type": analysis.primary_wound_type,
            "primary_severity": analysis.primary_severity,
            "primary_firstaidguide_id": analysis.primary_firstaidguide_id,
            "firstaid_snapshot": analysis.firstaid_snapshot,
            "analyzed_at": analysis.analyzed_at,
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at,
            "is_deleted": analysis.is_deleted,

            # Computed properties (avoid lazy loading)
            "is_successful_analysis": analysis.total_detections >= 0 and analysis.primary_wound_type in ["wound", "not_wound"] and analysis.primary_severity in ["mild", "moderate", "severe"],
            "has_multiple_wounds": analysis.total_detections > 1,
            "is_wound_detected": analysis.primary_wound_type == "wound",
            "meets_accuracy_threshold": avg_confidence >= DetectionProcessor.MIN_CONFIDENCE_THRESHOLD,

            # Use calculated values instead of lazy-loaded properties
            "average_confidence": avg_confidence,
            "significant_wounds": [w.dict() for w in significant_wounds]
        }

        logger.debug(
            f"[MAPPER] Built response: {analysis.analysis_id}, "
            f"avg_conf={avg_confidence:.2%}, wounds={len(significant_wounds)}"
        )

        return WoundAnalysisResponse(**response_data)

    @staticmethod
    def to_analysis_history_response(analyses: List) -> Dict[str, Any]:
        """
        Map list of WoundAnalysis entities sang history response.
        """
        total = len(analyses)
        successful = sum(1 for a in analyses if a.is_successful_analysis)
        avg_accuracy = (
            sum(a.average_confidence for a in analyses) / total
            if total > 0 else 0
        )

        return {
            "analyses": [a.to_response_dict() for a in analyses],
            "statistics": {
                "total_analyses": total,
                "successful_analyses": successful,
                "success_rate": (successful / total * 100) if total > 0 else 0,
                "average_accuracy": avg_accuracy,
                "meets_accuracy_threshold": (
                    avg_accuracy >= DetectionProcessor.MIN_CONFIDENCE_THRESHOLD
                )
            }
        }