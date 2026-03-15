from app.modules.ai.utils.wound_parser import WoundParser
from app.modules.ai.constants import WoundConstants
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
import logging
import uuid
from datetime import datetime, timezone

from app.modules.ai.models.wound_analysis import WoundAnalysis
from app.modules.ai.models.wound_detection import WoundDetection
from app.modules.firstaid.service import FirstAidService
from app.modules.firstaid.repository import FirstAidRepository
from app.modules.ai.repository.wound_analysis_repository import WoundAnalysisRepository
from app.modules.ai.exceptions import WoundAnalysisNotFoundError

logger = logging.getLogger(__name__)


class WoundAnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = WoundAnalysisRepository(db)
        self.first_aid_service = FirstAidService(FirstAidRepository(db), db)



    async def create_analysis(
        self,
        user_id: Optional[uuid.UUID],
        session_id: Optional[uuid.UUID],
        image_url: str,
        file_name: str,
        file_size: int,
        ai_model_version: str,
        total_detections: int,
        processing_time_ms: int
    ) -> WoundAnalysis:
        try:
            analysis = WoundAnalysis.create_analysis(
                user_id=user_id,
                session_id=session_id,
                image_url=image_url,
                file_name=file_name,
                file_size=file_size,
                ai_model_version=ai_model_version,
                total_detections=total_detections,
                processing_time_ms=processing_time_ms
            )

            result = await self.repository.create_analysis(analysis)

            status = "no wounds" if total_detections == 0 else f"{total_detections} wounds"
            identifier = f"user {user_id}" if user_id else f"session {session_id}"

            logger.info(
                f"Created analysis ({status}): {result.analysis_id} "
                f"({identifier})"
            )

            return result
        except Exception as e:
            logger.error(f"Failed to create analysis: {e}")
            raise

    async def get_first_aid_guide_for_detection(
        self,
        detection: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get matching first aid guide for detection"""
        original_wound_type = detection.get("wound_type", "unknown")
        original_severity = detection.get("severity", "mild")

        logger.info(
            f"[GET_FIRST_AID] Raw input: wound_type='{original_wound_type}', severity='{original_severity}'"
        )

        wound_info = WoundParser.parse_from_separate_fields(
            original_wound_type,
            original_severity
        )

        logger.info(
            f"[GET_FIRST_AID] After parse: wound_type='{wound_info['wound_type']}', "
            f"severity='{wound_info['severity']}', sub_type='{wound_info['sub_type']}'"
        )

        mapped_wound_type = WoundParser.map_wound_type_for_database(
            wound_info["wound_type"])

        logger.info(
            f"[FIRST_AID_LOOKUP] wound_type='{mapped_wound_type}', "
            f"severity='{wound_info['severity']}', sub_type='{wound_info['sub_type']}'"
        )

        guide = await self.first_aid_service.get_guide(
            wound_type=mapped_wound_type,
            severity=wound_info["severity"],
            sub_type=wound_info["sub_type"]
        )

        if guide:
            logger.info(
                f"[FIRST_AID_LOOKUP] Found guide: {guide.title} "
                f"(wound_type={guide.wound_type}, severity={guide.severity}, sub_type={guide.sub_type})"
            )
        else:
            logger.warning(
                f"[FIRST_AID_LOOKUP] No guide found for wound_type='{mapped_wound_type}', "
                f"severity='{wound_info['severity']}', sub_type='{wound_info['sub_type']}'"
            )

        return guide

    @staticmethod
    def _extract_source_string(source_data: Optional[Any]) -> Optional[str]:
        """Extract source string from JSONB or return as is"""
        if not source_data:
            return None
        if isinstance(source_data, str):
            return source_data
        if isinstance(source_data, dict):
            return source_data.get("source")
        return None

    @staticmethod
    def extract_snapshot(guide: Optional[Any]) -> Dict[str, Any]:
        """Create snapshot of first aid guide"""
        from app.modules.firstaid.models.firstaid_guide import FirstAidGuide
        
        if not guide:
            return {
                "title": "No first aid guide",
                "source": None,
                "steps": [],
                "dos": [],
                "donts": [],
                "supplies_needed": [],
                "estimated_healing_time": None
            }

        if isinstance(guide, FirstAidGuide):
            return {
                "title": guide.title,
                "source": WoundAnalysisService._extract_source_string(guide.source),
                "steps": FirstAidGuide.extract_list(guide.steps),
                "dos": FirstAidGuide.extract_list(guide.dos),
                "donts": FirstAidGuide.extract_list(guide.donts),
                "supplies_needed": FirstAidGuide.extract_list(guide.supplies_needed),
                "estimated_healing_time": guide.estimated_healing_time,
            }
        
        # Fallback for dict (backward compatibility)
        return {
            "title": guide.get("title", ""),
            "source": WoundAnalysisService._extract_source_string(guide.get("source")),
            "steps": guide.get("steps", []),
            "dos": guide.get("dos", []),
            "donts": guide.get("donts", []),
            "supplies_needed": guide.get("supplies_needed", []),
            "estimated_healing_time": guide.get("estimated_healing_time"),
        }

    @staticmethod
    def extract_guide_id(guide: Optional[Any]) -> Optional[uuid.UUID]:
        """Extract guide ID from guide"""
        from app.modules.firstaid.models.firstaid_guide import FirstAidGuide
        
        if not guide:
            return None

        if isinstance(guide, FirstAidGuide):
            return guide.firstaidguide_id
        
        guide_id = guide.get("firstaidguide_id")
        if not guide_id:
            return None

        try:
            return uuid.UUID(str(guide_id)) if not isinstance(guide_id, uuid.UUID) else guide_id
        except (ValueError, AttributeError):
            logger.warning(f"Invalid guide_id format: {guide_id}")
            return None

    async def _process_detection_data(
        self,
        detection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process detection data: parse wound info and fetch first aid guide.
        Returns dict with parsed data ready for WoundDetection creation.
        """
        original_wound_type = detection.get("wound_type", "unknown")
        original_severity = detection.get("severity", "mild")

        wound_info = WoundParser.parse_from_separate_fields(
            original_wound_type,
            original_severity
        )
        mapped_wound_type = WoundParser.map_wound_type_for_database(
            wound_info["wound_type"])

        guide = await self.get_first_aid_guide_for_detection(detection)
        guide_id = self.extract_guide_id(guide)
        snapshot = self.extract_snapshot(guide)

        return {
            "wound_type": mapped_wound_type,
            "severity": wound_info["severity"],
            "sub_type": wound_info["sub_type"],
            "guide_id": guide_id,
            "snapshot": snapshot,
        }

    async def save_detections(
        self,
        analysis_id: uuid.UUID,
        detections: List[Dict[str, Any]]
    ) -> None:
        """Save wound detections to database"""
        detection_objects = []

        for detection in detections:
            processed = await self._process_detection_data(detection)

            wound_detection = WoundDetection(
                analysis_id=analysis_id,
                wound_type=processed["wound_type"],
                severity=processed["severity"],
                sub_type=processed["sub_type"],
                confidence_score=detection.get("confidence", 0.0),
                bounding_box=detection.get("bounding_box", {}),
                detection_index=detection.get("detection_index", 0),
                firstaidguide_id=processed["guide_id"],
                firstaid_snapshot=processed["snapshot"],
                created_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            detection_objects.append(wound_detection)

        if detection_objects:
            await self.repository.add_detections(detection_objects)

        logger.info(
            f"Saved {len(detections)} detections for analysis {analysis_id}")

    async def get_history(
        self,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[uuid.UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[WoundAnalysis]:
        """Get analysis history"""
        analyses, _ = await self.repository.get_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            offset=offset
        )
        return analyses

    async def get_analysis_by_id(
        self,
        analysis_id: uuid.UUID
    ) -> Optional[WoundAnalysis]:
        """Get wound analysis by ID"""
        return await self.repository.get_analysis_by_id(analysis_id)

    async def get_by_id(self, analysis_id: uuid.UUID) -> Optional[WoundAnalysis]:
        return await self.get_analysis_by_id(analysis_id)

    async def soft_delete_analysis(self, analysis_id: uuid.UUID) -> None:
        """Soft delete analysis"""
        success = await self.repository.soft_delete_analysis(analysis_id)
        if success:
            logger.info(f"Soft deleted analysis: {analysis_id}")
        else:
            logger.warning(f"Analysis not found for deletion: {analysis_id}")
