from typing import Any, Dict, List, Optional
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
        user_responses: Optional[List[Any]] = None,
    ) -> Dict:
        response = {
            'analysis_id': str(analysis.analysis_id),
            'image_url': analysis.image_url,
            'file_name': analysis.image_url.split('/')[-1] if analysis.image_url else '',
            'file_size': analysis.image_size_bytes or 0,
            'ai_model_version': analysis.model_version or '',
            'total_detections': len(analysis.wound_detections) if hasattr(analysis, 'wound_detections') and analysis.wound_detections else 0,
            'processing_time_ms': 0,
            'analyzed_at': analysis.completed_at.isoformat() if analysis.completed_at else analysis.created_at.isoformat(),
            'created_at': analysis.created_at.isoformat(),
            'is_guest_analysis': analysis.is_guest_analysis
        }

        if analysis.user_id:
            response['user_id'] = str(analysis.user_id)
        if analysis.guest_session_id:
            response['guest_session_id'] = str(analysis.guest_session_id)

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
                
        if user_responses is not None:
            response['user_responses'] = [
                {
                    'response_id': str(r.response_id),
                    'question_id': str(r.question_id),
                    'answer_id': str(r.answer_id),
                    'created_at': r.created_at.isoformat()
                } for r in user_responses
            ]
            
        return response

    @staticmethod
    def map_wound_analysis_basic(analysis: Any) -> Dict:
        insp = inspect(analysis)
        wound_detections_attr = insp.attrs.wound_detections
        if wound_detections_attr.loaded_value is not NO_VALUE:
            total_detections = len(analysis.wound_detections) if analysis.wound_detections else 0
        else:
            total_detections = 0

        return {
            'analysis_id': str(analysis.analysis_id),
            'image_url': analysis.image_url,
            'file_name': analysis.image_url.split('/')[-1] if analysis.image_url else '',
            'file_size': analysis.image_size_bytes or 0,
            'ai_model_version': analysis.model_version or '',
            'total_detections': total_detections,
            'processing_time_ms': 0,
            'analyzed_at': analysis.completed_at.isoformat() if analysis.completed_at else analysis.created_at.isoformat(),
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
            'confidence_score': getattr(detection, 'confidence', getattr(detection, 'confidence_score', 0.0)),
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
