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
from app.modules.ai.repository.wound_analysis_repository import WoundAnalysisRepository
from app.modules.ai.exceptions import WoundAnalysisNotFoundError

logger = logging.getLogger(__name__)


class WoundAnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = WoundAnalysisRepository(db)
        self.first_aid_service = FirstAidService(db)

    @classmethod
    def map_wound_type_for_database(cls, ai_wound_type: str) -> str:
        """Map wound type from AI to database format"""
        if ai_wound_type.lower().startswith("burn"):
            return "burn"

        normalized = ai_wound_type.lower().strip()

        if normalized not in WoundConstants.WOUND_TYPES:
            logger.warning(
                f"Wound type '{normalized}' not supported, "
                f"using 'abrasion' as fallback"
            )
            return "abrasion"

        return normalized

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
        """Create wound analysis record"""
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

        wound_info = WoundParser.parse_from_separate_fields(
            original_wound_type,
            original_severity
        )

        mapped_wound_type = self.map_wound_type_for_database(
            wound_info["wound_type"])

        guide = await self.first_aid_service.get_first_aid_guide(
            wound_type=mapped_wound_type,
            severity=wound_info["severity"],
            sub_type=wound_info["sub_type"]
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
    def extract_snapshot(guide: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create snapshot of first aid guide"""
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
    def extract_guide_id(guide: Optional[Dict[str, Any]]) -> Optional[uuid.UUID]:
        """Extract guide ID from guide dictionary"""
        if not guide:
            return None

        guide_id = guide.get("firstaidguide_id")
        if not guide_id:
            return None

        try:
            return uuid.UUID(str(guide_id)) if not isinstance(guide_id, uuid.UUID) else guide_id
        except (ValueError, AttributeError):
            logger.warning(f"Invalid guide_id format: {guide_id}")
            return None

    async def save_detections(
        self,
        analysis_id: uuid.UUID,
        detections: List[Dict[str, Any]]
    ) -> None:
        """Save wound detections to database"""
        detection_objects = []

        for detection in detections:
            original_wound_type = detection.get("wound_type", "unknown")
            original_severity = detection.get("severity", "mild")

            wound_info = WoundParser.parse_from_separate_fields(
                original_wound_type,
                original_severity
            )
            mapped_wound_type = self.map_wound_type_for_database(
                wound_info["wound_type"])

            # Get first aid guide
            guide = await self.get_first_aid_guide_for_detection(detection)
            guide_id = self.extract_guide_id(guide)
            snapshot = self.extract_snapshot(guide)

            # Create detection record
            wound_detection = WoundDetection(
                analysis_id=analysis_id,
                wound_type=mapped_wound_type,
                severity=wound_info["severity"],
                sub_type=wound_info["sub_type"],
                confidence_score=detection.get("confidence", 0.0),
                bounding_box=detection.get("bounding_box", {}),
                detection_index=detection.get("detection_index", 0),
                firstaidguide_id=guide_id,
                firstaid_snapshot=snapshot,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            detection_objects.append(wound_detection)

        if detection_objects:
            await self.repository.add_detections(detection_objects)
            # Commit handled by repository flush/commit or manual commit here?
            # Repository add_detections uses flush. We should commit.
            await self.db.commit()

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
