from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, desc
from typing import Dict, Any, List, Optional
import logging
import uuid

from app.modules.ai.models.wound_analysis import WoundAnalysis
from app.modules.ai.models.wound_detection import WoundDetection
from app.modules.ai.services.detection_processor import DetectionProcessor
from app.modules.firstaid.services.first_aid_service import FirstAidService

logger = logging.getLogger(__name__)


class WoundAnalysisService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.first_aid_service = FirstAidService(db)

    async def get_first_aid_guide_for_detection(
        self,
        detection: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        original_wound_type = detection.get("wound_type", "unknown")
        detection_severity = detection.get("severity", "mild")

        mapped_wound_type = DetectionProcessor.map_wound_type_for_database(
            original_wound_type
        )

        if original_wound_type.lower() == "burn":
            return await self._get_burn_guide(original_wound_type, detection_severity)

        # For non-burn, use base severity to match firstaid_guides
        base_severity = DetectionProcessor.extract_base_severity(detection_severity)

        logger.info(
            f"Getting guide for {original_wound_type}/{detection_severity} "
            f"(mapped: {mapped_wound_type}, base_severity: {base_severity})"
        )

        return await self.first_aid_service.get_first_aid_guide(
            wound_type=mapped_wound_type,
            severity=base_severity
        )

    async def _get_burn_guide(
        self,
        wound_type: str,
        severity: str
    ) -> Optional[Dict[str, Any]]:
        base_type, parsed_severity, sub_type = DetectionProcessor.parse_burn_classification(
            wound_type,
            severity
        )

        logger.info(
            f"Burn guide search: {wound_type}/{severity} "
            f"-> {base_type}/{parsed_severity}"
            f"{f'/{sub_type}' if sub_type else ''}"
        )

        guide = await self.first_aid_service.get_first_aid_guide(
            wound_type=base_type,
            severity=parsed_severity,
            sub_type=sub_type if sub_type else None
        )

        if guide:
            sub_info = f" (sub_type: {guide.get('sub_type')})" if guide.get('sub_type') else ""
            logger.info(f"Found: {guide.get('title')}{sub_info}")
        else:
            logger.warning(f"No guide found for {base_type}/{parsed_severity}")

        return guide

    @staticmethod
    def extract_guide_id(guide: Optional[Dict[str, Any]]) -> Optional[uuid.UUID]:
        if not guide:
            return None
        guide_id_str = guide.get("firstaidguide_id")
        if guide_id_str:
            return uuid.UUID(guide_id_str)
        return None

    @staticmethod
    def extract_snapshot(guide: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not guide:
            return {
                "title": "Không có hướng dẫn sơ cứu",
                "description": "Không tìm thấy hướng dẫn phù hợp",
                "steps": [],
                "warnings": [],
                "dos": [],
                "donts": []
            }

        return {
            "title": guide.get("title", ""),
            "description": guide.get("description"),
            "steps": guide.get("steps", []),
            "warnings": guide.get("warnings", []),
            "dos": guide.get("dos", []),
            "donts": guide.get("donts", []),
            "supplies_needed": guide.get("supplies_needed", []),
            "estimated_healing_time": guide.get("estimated_healing_time"),
        }

    async def create_no_wound_analysis(
        self,
        user_id: Optional[uuid.UUID],
        image_url: str,
        file_name: str,
        file_size: int,
        ai_model_version: str,
        processing_time_ms: int,
        total_detections: int = 0
    ) -> WoundAnalysis:
        analysis = WoundAnalysis.create_analysis(
            user_id=user_id,
            image_url=image_url,
            file_name=file_name,
            file_size=file_size,
            ai_model_version=ai_model_version,
            total_detections=total_detections,
            processing_time_ms=processing_time_ms
        )

        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(analysis)

        logger.info(
            f"Created no-wound analysis: {analysis.analysis_id} "
            f"(user: {user_id or 'guest'})"
        )

        return analysis

    async def create_wound_analysis(
        self,
        user_id: Optional[uuid.UUID],
        image_url: str,
        file_name: str,
        file_size: int,
        ai_model_version: str,
        total_detections: int,
        processing_time_ms: int
    ) -> WoundAnalysis:
        analysis = WoundAnalysis.create_analysis(
            user_id=user_id,
            image_url=image_url,
            file_name=file_name,
            file_size=file_size,
            ai_model_version=ai_model_version,
            total_detections=total_detections,
            processing_time_ms=processing_time_ms
        )

        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(analysis)

        logger.info(
            f"Created wound analysis: {analysis.analysis_id} "
            f"(user: {user_id or 'guest'})"
        )

        return analysis

    async def save_detections(
        self,
        analysis_id: uuid.UUID,
        detections: List[Dict[str, Any]]
    ) -> None:
        for detection in detections:
            original_wound_type = detection.get("wound_type", "unknown")
            mapped_wound_type = DetectionProcessor.map_wound_type_for_database(
                original_wound_type
            )

            # Get guide for each detection
            guide = await self.get_first_aid_guide_for_detection(detection)
            guide_id = self.extract_guide_id(guide)
            snapshot = self.extract_snapshot(guide)

            parsed_severity, sub_type = DetectionProcessor.get_parsed_severity_for_storage(
                original_wound_type,
                detection.get("severity", "mild")
            )

            wound_detection = WoundDetection.create_detection(
                analysis_id=analysis_id,
                wound_type=mapped_wound_type,
                severity=parsed_severity,
                sub_type=sub_type,
                confidence_score=detection.get("confidence", 0.0),
                bounding_box=detection.get("bounding_box", {}),
                detection_index=detection.get("detection_index", 0),
                firstaidguide_id=guide_id,
                firstaid_snapshot=snapshot
            )
            self.db.add(wound_detection)

        await self.db.commit()
        logger.info(f"Saved {len(detections)} detections for analysis {analysis_id}")

    async def get_user_analysis_history(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0
    ) -> List[WoundAnalysis]:
        query = (
            select(WoundAnalysis)
            .options(selectinload(WoundAnalysis.wound_detections))
            .where(
                WoundAnalysis.user_id == user_id,
                WoundAnalysis.is_deleted == False
            )
            .order_by(desc(WoundAnalysis.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        analyses = result.scalars().all()

        logger.info(
            f"Retrieved {len(analyses)} analyses for user {user_id} "
            f"(limit: {limit}, offset: {offset})"
        )

        return list(analyses)

    async def get_analysis_by_id(
        self,
        analysis_id: uuid.UUID
    ) -> Optional[WoundAnalysis]:
        query = (
            select(WoundAnalysis)
            .options(selectinload(WoundAnalysis.wound_detections))
            .where(
                WoundAnalysis.analysis_id == analysis_id,
                WoundAnalysis.is_deleted == False
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_detections_for_analysis(
        self,
        analysis_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        from app.modules.firstaid.models.firstaid_guide import FirstAidGuide

        query = (
            select(WoundDetection, FirstAidGuide)
            .outerjoin(FirstAidGuide, WoundDetection.firstaidguide_id == FirstAidGuide.firstaidguide_id)
            .where(WoundDetection.analysis_id == analysis_id)
            .order_by(WoundDetection.detection_index)
        )

        result = await self.db.execute(query)
        rows = result.all()

        detections = []
        for detection, guide in rows:
            snapshot = self.extract_snapshot({
                "title": guide.title if guide else "Không có hướng dẫn",
                "description": guide.description if guide else "",
                "steps": guide.steps if guide else [],
                "warnings": guide.warnings if guide else [],
                "dos": guide.dos if guide else [],
                "donts": guide.donts if guide else [],
                "supplies_needed": guide.supplies_needed if guide else [],
                "estimated_healing_time": guide.estimated_healing_time if guide else ""
            })

            detections.append({
                "detection_id": str(detection.detection_id),
                "wound_type": detection.wound_type,
                "severity": detection.severity,
                "sub_type": detection.sub_type,
                "confidence_score": detection.confidence_score,
                "bounding_box": detection.bounding_box,
                "detection_index": detection.detection_index,
                "firstaid_snapshot": snapshot
            })

        return detections

    async def soft_delete_analysis(self, analysis_id: uuid.UUID) -> None:
        analysis = await self.get_analysis_by_id(analysis_id)

        if analysis:
            analysis.mark_as_deleted()
            await self.db.commit()
            logger.info(f"Soft deleted analysis: {analysis_id}")
        else:
            logger.warning(f"Analysis not found for deletion: {analysis_id}")