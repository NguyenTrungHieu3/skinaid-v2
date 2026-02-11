from typing import Any, Dict
from uuid import UUID
from datetime import datetime
from sqlalchemy import inspect
from sqlalchemy.orm.attributes import NO_VALUE


class ResponseMapper:

    @staticmethod
    def map_wound_analysis(
        analysis: Any,
        include_detections: bool = True,
        include_firstaid_details: bool = True,
    ) -> Dict:
        response = {
            'analysis_id': str(analysis.analysis_id),
            'image_url': analysis.image_url,
            'file_name': analysis.file_name,
            'file_size': analysis.file_size,
            'ai_model_version': analysis.ai_model_version,
            'total_detections': analysis.total_detections,
            'processing_time_ms': analysis.processing_time_ms,
            'analyzed_at': analysis.analyzed_at.isoformat(),
            'created_at': analysis.created_at.isoformat(),
            'is_guest_analysis': analysis.is_guest_analysis
        }

        if analysis.user_id:
            response['user_id'] = str(analysis.user_id)
        if analysis.session_id:
            response['session_id'] = str(analysis.session_id)

        if include_detections:
            insp = inspect(analysis)
            wound_detections_attr = insp.attrs.wound_detections

            if wound_detections_attr.loaded_value is not NO_VALUE:
                response['significant_wounds'] = [
                    ResponseMapper.map_wound_detection(
                        d, include_firstaid_details)
                    for d in analysis.wound_detections
                ]
            else:
                response['significant_wounds'] = []
        return response

    @staticmethod
    def map_wound_analysis_basic(analysis: Any) -> Dict:
        """Basic response for POST /ai/analyze — thông tin tối thiểu."""
        return {
            'analysis_id': str(analysis.analysis_id),
            'image_url': analysis.image_url,
            'file_name': analysis.file_name,
            'file_size': analysis.file_size,
            'ai_model_version': analysis.ai_model_version,
            'total_detections': analysis.total_detections,
            'processing_time_ms': analysis.processing_time_ms,
            'analyzed_at': analysis.analyzed_at.isoformat(),
            'is_guest_analysis': analysis.is_guest_analysis
        }

    @staticmethod
    def map_wound_detection(
        detection: Any,
        include_firstaid_details: bool = True,
    ) -> Dict:
        base_response = {
            'detection_id': str(detection.detection_id),
            'wound_type': detection.wound_type,
            'severity': detection.severity,
            'sub_type': detection.sub_type,
            'confidence_score': detection.confidence_score,
            'bounding_box': detection.bounding_box,
            'detection_index': detection.detection_index,
            'firstaid_guide_id': (
                str(detection.firstaidguide_id)
                if detection.firstaidguide_id
                else None
            ),
        }

        if include_firstaid_details:
            base_response['firstaid_snapshot'] = detection.firstaid_snapshot

        return base_response
