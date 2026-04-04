from app.modules.ai.utils.wound_parser import WoundParser
from app.modules.ai.constants import WoundConstants
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from uuid import uuid4, UUID
from datetime import datetime, timezone

from app.modules.ai.models.analysis import Analysis
from app.modules.ai.models.detection import Detection
from app.modules.firstaid.service import FirstAidService
from app.modules.firstaid.repository import FirstAidRepository
from app.modules.ai.repository.wound_analysis_repository import WoundAnalysisRepository
from app.modules.ai.exceptions import WoundAnalysisNotFoundError


class WoundAnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = WoundAnalysisRepository(db)
        self.first_aid_service = FirstAidService(FirstAidRepository(db), db)



    async def create_analysis(
        self,
        user_id: Optional[UUID],
        guest_session_id: Optional[UUID],
        image_url: str,
        image_size_bytes: int,
    ) -> Analysis:
        analysis = Analysis.create_analysis(
            user_id=user_id,
            guest_session_id=guest_session_id,
            image_url=image_url,
            image_size_bytes=image_size_bytes
        )

        return await self.repository.create_analysis(analysis)

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

        mapped_wound_type = WoundParser.map_wound_type_for_database(
            wound_info["wound_type"])

        guide = await self.first_aid_service.get_guide(
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
    def extract_guide_id(guide: Optional[Any]) -> Optional[UUID]:
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
            return UUID(str(guide_id)) if not isinstance(guide_id, UUID) else guide_id
        except (ValueError, AttributeError):
            return None

    async def _process_detection_data(
        self,
        detection: Dict[str, Any]
    ) -> Dict[str, Any]:
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
            # sub_type là field riêng từ AI service — WoundParser chỉ parse được
            # khi sub_type nhúng trong chuỗi severity (vd "moderate_skintear").
            # Dùng detection.get("sub_type") làm nguồn ưu tiên.
            "sub_type": detection.get("sub_type") or wound_info["sub_type"],
            "guide_id": guide_id,
            "snapshot": snapshot,
        }

    async def save_detections(
        self,
        analysis_id: UUID,
        detections: List[Dict[str, Any]]
    ) -> None:
        """Save wound detections to database"""
        detection_objects = []

        for detection in detections:
            processed = await self._process_detection_data(detection)

            wound_detection = Detection(
                analysis_id=analysis_id,
                detected_class=detection.get("detected_class", detection.get("class_name", "skin_wound")),
                wound_type=processed["wound_type"],
                severity=processed["severity"],
                sub_type=processed["sub_type"],
                confidence=float(detection.get("confidence", 0.0)),
                bounding_box=detection.get("bounding_box", {}),
                detection_index=detection.get("detection_index", 0),
                firstaidguide_id=processed["guide_id"],
                firstaid_snapshot=processed["snapshot"],
                created_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            detection_objects.append(wound_detection)

        if detection_objects:
            await self.repository.add_detections(detection_objects)

    async def update_analysis_after_processing(
        self,
        analysis_id: UUID,
        detections: List[Dict[str, Any]],
        ai_model_version: Optional[str] = None,
        started_at: Optional[datetime] = None,
    ) -> None:
        """
        Update Analysis record after AI processing completes:
        - Set status = "completed"
        - Fill completed_at, started_at
        - Populate top-level wound_type / severity / sub_type / confidence
          from the primary (highest confidence) detection.
        """
        completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        primary: Optional[Dict[str, Any]] = None
        if detections:
            primary = max(detections, key=lambda d: float(d.get("confidence", 0.0)))

        wound_type = None
        severity = None
        sub_type = None
        confidence = None

        if primary:
            wound_info = WoundParser.parse_from_separate_fields(
                primary.get("wound_type", "unknown"),
                primary.get("severity", "mild"),
            )
            wound_type = WoundParser.map_wound_type_for_database(wound_info["wound_type"])
            severity = wound_info["severity"]
            sub_type = primary.get("sub_type") or wound_info["sub_type"]
            confidence = float(primary.get("confidence", 0.0))

        await self.repository.update_analysis_status(
            analysis_id=analysis_id,
            status="completed",
            started_at=started_at,
            completed_at=completed_at,
            wound_type=wound_type,
            severity=severity,
            sub_type=sub_type,
            confidence=confidence,
            model_version=ai_model_version,
        )

    async def get_history(
        self,
        user_id: Optional[UUID] = None,
        guest_session_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Analysis]:
        """Get analysis history"""
        analyses, _ = await self.repository.get_history(
            user_id=user_id,
            guest_session_id=guest_session_id,
            limit=limit,
            offset=offset
        )
        return analyses

    async def get_analysis_by_id(
        self,
        analysis_id: UUID
    ) -> Optional[Analysis]:
        """Get wound analysis by ID"""
        return await self.repository.get_analysis_by_id(analysis_id)

    async def get_by_id(self, analysis_id: UUID) -> Optional[Analysis]:
        return await self.get_analysis_by_id(analysis_id)

    async def soft_delete_analysis(self, analysis_id: UUID) -> None:
        """Soft delete analysis"""
        await self.repository.soft_delete_analysis(analysis_id)

    async def persist_llm_guidance(
        self,
        analysis_id: UUID,
        wound_type: str,
        severity: str,
        structured_guidance: Dict[str, Any],
    ) -> int:
        """
        Lưu structured_guidance từ LLM vào Detection.firstaid_snapshot.
        Ghi đè snapshot cũ (từ B4 DB lookup) bằng output phong phú hơn từ LLM.
        Trả về số detections đã được update.
        """
        snapshot = {
            "title": structured_guidance.get("title", ""),
            "steps": structured_guidance.get("steps", []),
            "dos": structured_guidance.get("dos", []),
            "donts": structured_guidance.get("donts", []),
            "supplies_needed": structured_guidance.get("supplies_needed", []),
            "estimated_healing_time": structured_guidance.get("estimated_healing_time"),
            "source": structured_guidance.get("source"),
            "llm_generated": True,
        }
        return await self.repository.update_detection_snapshot(
            analysis_id=analysis_id,
            wound_type=wound_type,
            severity=severity,
            snapshot=snapshot,
        )
