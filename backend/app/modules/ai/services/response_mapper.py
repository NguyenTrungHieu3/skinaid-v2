from typing import List, Dict, Any
from app.modules.ai.schemas.wound_analysis_schemas import WoundAnalysisResponse, SimpleAnalysisResponse
from app.modules.ai.schemas.wound_detection_schemas import (
    WoundDetectionSummary,
    WoundDetectionResponse 
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
        avg_confidence = (
            sum(d.get("confidence_score", 0.0) for d in significant_detections) /
            len(significant_detections)
            if significant_detections else 0.0
        )

        significant_wounds = []
        wound_guides = {}
        for detection in significant_detections:
            det_wound_type = detection.get("wound_type", "unknown")
            mapped_wound_type = DetectionProcessor.map_wound_type_for_database(det_wound_type)
            parsed_severity = detection.get("severity", "mild")
            sub_type = detection.get("sub_type")

            wound_summary = WoundDetectionSummary(
                wound_type=mapped_wound_type,
                severity=parsed_severity,
                sub_type=sub_type,
                confidence_score=detection.get("confidence_score", 0.0),
                bounding_box=detection.get("bounding_box", {}),
                firstaid_snapshot=detection.get("firstaid_snapshot")
            )
            significant_wounds.append(wound_summary)

            # Group by wound_type for wound_guides
            if mapped_wound_type not in wound_guides:
                wound_guides[mapped_wound_type] = []
            wound_guides[mapped_wound_type].append({
                "severity": parsed_severity,
                "sub_type": sub_type,
                "firstaid_snapshot": detection.get("firstaid_snapshot")
            })

        is_successful = analysis.total_detections >= 0

        response_data = {
            "analysis_id": analysis.analysis_id,
            "user_id": analysis.user_id,
            "image_url": analysis.image_url,
            "file_name": analysis.file_name,
            "file_size": analysis.file_size,
            "ai_model_version": analysis.ai_model_version,
            "total_detections": analysis.total_detections,
            "processing_time_ms": analysis.processing_time_ms,
            "processing_time_seconds": (
                round(analysis.processing_time_ms / 1000, 3)
                if analysis.processing_time_ms > 0
                else None
            ),
            "analyzed_at": analysis.analyzed_at,
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at,
            "is_deleted": analysis.is_deleted,

            "is_successful_analysis": is_successful,
            "has_multiple_wounds": analysis.total_detections > 1,
            "is_wound_detected": analysis.total_detections > 0,
            "is_guest_analysis": analysis.user_id is None,

            "average_confidence": avg_confidence,
            "meets_accuracy_threshold": avg_confidence >= DetectionProcessor.MIN_CONFIDENCE_THRESHOLD,

            "significant_wounds": [
                w.model_dump() if hasattr(w, 'model_dump') else w.dict()
                for w in significant_wounds
            ],
            "wound_guides": wound_guides
        }

        logger.debug(
            f"[MAPPER] {analysis.analysis_id}, "
            f"user: {analysis.user_id or 'guest'}, "
            f"conf={avg_confidence:.2%}"
        )

        return WoundAnalysisResponse(**response_data)

    @staticmethod
    def to_simple_analysis_response(analysis) -> SimpleAnalysisResponse:
        
        response_data = {
            "analysis_id": analysis.analysis_id,
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at
        }
        return SimpleAnalysisResponse(**response_data)

    @staticmethod
    def to_detection_response(detection) -> WoundDetectionResponse:
        return WoundDetectionResponse(
            detection_id=detection.detection_id,
            analysis_id=detection.analysis_id,
            wound_type=detection.wound_type,
            severity=detection.severity,
            sub_type=detection.sub_type,
            confidence_score=detection.confidence_score,
            bounding_box=detection.bounding_box,
            detection_index=detection.detection_index,
            firstaidguide_id=detection.firstaidguide_id,
            firstaid_snapshot=detection.firstaid_snapshot,
            created_at=detection.created_at
        )

    @staticmethod
    def to_analysis_history_response(analyses: List) -> Dict[str, Any]:
        
        total = len(analyses)
        successful = sum(
            1 for a in analyses
            if a.total_detections >= 0
        )
        
        total_confidence = 0.0
        count = 0
        
        for analysis in analyses:
            if 'wound_detections' in analysis.__dict__ and analysis.wound_detections:
                for detection in analysis.wound_detections:
                    total_confidence += detection.confidence_score
                    count += 1
        
        avg_accuracy = (total_confidence / count) if count > 0 else 0.0
        analyses_data = []
        for a in analyses:
            analyses_data.append({
                "analysis_id": a.analysis_id,
                "user_id": a.user_id,
                "is_guest_analysis": a.user_id is None,
                "image_url": a.image_url,
                "file_name": a.file_name,
                "file_size": a.file_size,
                "ai_model_version": a.ai_model_version,
                "total_detections": a.total_detections,
                "processing_time_ms": a.processing_time_ms,
                "processing_time_seconds": round(a.processing_time_ms / 1000, 3) if a.processing_time_ms > 0 else None,
                "analyzed_at": a.analyzed_at,
                "created_at": a.created_at,
                "updated_at": a.updated_at,
                "is_deleted": a.is_deleted,
                "is_successful_analysis": a.total_detections >= 0,
                "has_multiple_wounds": a.total_detections > 1,
                "is_wound_detected": a.total_detections > 0,
                "average_confidence": a.average_confidence,
                "meets_accuracy_threshold": a.average_confidence >= 0.65,
            })

        return {
            "analyses": analyses_data,
            "statistics": {
                "total_analyses": total,
                "successful_analyses": successful,
                "success_rate": (successful / total * 100) if total > 0 else 0,
                "average_accuracy": avg_accuracy,
                "meets_accuracy_threshold": avg_accuracy >= DetectionProcessor.MIN_CONFIDENCE_THRESHOLD,
                "guest_analyses": sum(1 for a in analyses if a.user_id is None),
                "authenticated_analyses": sum(1 for a in analyses if a.user_id is not None)
            }
        }