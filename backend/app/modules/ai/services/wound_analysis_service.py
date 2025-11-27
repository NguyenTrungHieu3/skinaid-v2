from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, desc
from typing import Dict, Any, List, Optional
import logging
import uuid

from app.modules.ai.models.wound_analysis import WoundAnalysis
from app.modules.ai.models.wound_detection import WoundDetection
from app.modules.firstaid.services.first_aid_service import FirstAidService

logger = logging.getLogger(__name__)


from app.modules.ai.constants import WoundConstants
from app.modules.ai.utils.wound_parser import WoundParser

class WoundAnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.first_aid_service = FirstAidService(db)
    @classmethod
    def map_wound_type_for_database(cls, ai_wound_type: str) -> str:
        """Map wound type từ AI sang database format"""
        if ai_wound_type.lower().startswith("burn"):
            return "burn"
        
        normalized = ai_wound_type.lower().strip()
        
        if normalized not in WoundConstants.WOUND_TYPES:
            logger.warning(
                f"Loại vết thương '{normalized}' không được hỗ trợ, "
                f"sử dụng 'abrasion' làm dự phòng"
            )
            return "abrasion"
        
        return normalized
    
    async def create_analysis(
        self,
        user_id: Optional[uuid.UUID],
        image_url: str,
        file_name: str,
        file_size: int,
        ai_model_version: str,
        total_detections: int,
        processing_time_ms: int
    ) -> WoundAnalysis:
        """Tạo wound analysis record (cho cả có/không vết thương)"""
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

        status = "không vết thương" if total_detections == 0 else f"{total_detections} vết thương"
        logger.info(
            f"Đã tạo phân tích ({status}): {analysis.analysis_id} "
            f"(user: {user_id or 'guest'})"
        )

        return analysis

    async def get_first_aid_guide_for_detection(
        self,
        detection: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Lấy first aid guide phù hợp cho detection"""
        original_wound_type = detection.get("wound_type", "unknown")
        original_severity = detection.get("severity", "mild")

        wound_info = WoundParser.parse_from_separate_fields(
            original_wound_type, 
            original_severity
        )
        
        mapped_wound_type = self.map_wound_type_for_database(wound_info["wound_type"])

        logger.info(
            f"Đang lấy hướng dẫn cho {original_wound_type}/{original_severity} "
            f"(đã ánh xạ: {mapped_wound_type}, "
            f"severity: {wound_info['severity']}, "
            f"sub_type: {wound_info['sub_type']})"
        )

        guide = await self.first_aid_service.get_first_aid_guide(
            wound_type=mapped_wound_type,
            severity=wound_info["severity"],
            sub_type=wound_info["sub_type"]
        )

        if guide:
            sub_info = f" (sub_type: {guide.get('sub_type')})" if guide.get('sub_type') else ""
            logger.info(f"Đã tìm thấy: {guide.get('title')}{sub_info}")
        else:
            logger.warning(
                f"Không tìm thấy hướng dẫn cho {mapped_wound_type}/"
                f"{wound_info['severity']}"
                f"{f'/{wound_info['sub_type']}' if wound_info['sub_type'] else ''}"
            )

        return guide

    @staticmethod
    def _extract_source_string(source_data: Optional[Any]) -> Optional[str]:
        """Extract source string from JSONB object or return string as-is"""
        if not source_data:
            return None
        if isinstance(source_data, str):
            return source_data
        if isinstance(source_data, dict):
            return source_data.get("source")
        return None

    @staticmethod
    def extract_snapshot(guide: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Tạo snapshot của first aid guide"""
        if not guide:
            return {
                "title": "Không có hướng dẫn sơ cứu",
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
        """Trích xuất guide ID từ guide dictionary"""
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
        """Lưu danh sách wound detections vào database"""
        for detection in detections:
            original_wound_type = detection.get("wound_type", "unknown")
            original_severity = detection.get("severity", "mild")
            
            wound_info = WoundParser.parse_from_separate_fields(
                original_wound_type,
                original_severity
            )
            mapped_wound_type = self.map_wound_type_for_database(wound_info["wound_type"])

            # Lấy first aid guide
            guide = await self.get_first_aid_guide_for_detection(detection)
            guide_id = self.extract_guide_id(guide)
            snapshot = self.extract_snapshot(guide)

            # Tạo detection record
            from datetime import datetime, timezone
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
            self.db.add(wound_detection)

        await self.db.commit()
        logger.info(f"Đã lưu {len(detections)} detections cho phân tích {analysis_id}")

    async def get_history(
        self,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[uuid.UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[WoundAnalysis]:
        """Lấy lịch sử phân tích cho user hoặc guest session"""
        query = select(WoundAnalysis).options(selectinload(WoundAnalysis.wound_detections))
        
        if user_id:
            query = query.where(WoundAnalysis.user_id == user_id)
        elif session_id:
            query = query.where(WoundAnalysis.session_id == session_id)
        
        query = (
            query.where(WoundAnalysis.is_deleted == False)
            .order_by(desc(WoundAnalysis.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        analyses = result.scalars().all()

        identifier = f"user {user_id}" if user_id else f"session {session_id}"
        logger.info(
            f"Đã lấy {len(analyses)} phân tích cho {identifier} "
            f"(limit: {limit}, offset: {offset})"
        )

        return list(analyses)

    async def get_analysis_by_id(
        self,
        analysis_id: uuid.UUID
    ) -> Optional[WoundAnalysis]:
        """Lấy wound analysis theo ID"""
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
    
    async def get_by_id(self, analysis_id: uuid.UUID) -> Optional[WoundAnalysis]:
        return await self.get_analysis_by_id(analysis_id)

    async def get_detections_for_analysis(
        self,
        analysis_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Lấy danh sách detections cho một analysis"""
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
            guide_dict = None
            if guide:
                guide_dict = {
                    "title": guide.title,
                    "source": guide.source,
                    "steps": guide.steps,
                    "dos": guide.dos,
                    "donts": guide.donts,
                    "supplies_needed": guide.supplies_needed,
                    "estimated_healing_time": guide.estimated_healing_time
                }
            
            snapshot = self.extract_snapshot(guide_dict)

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
        """Soft delete một wound analysis"""
        analysis = await self.get_analysis_by_id(analysis_id)

        if analysis:
            analysis.mark_as_deleted()
            await self.db.commit()
            logger.info(f"Đã xóa mềm phân tích: {analysis_id}")
        else:
            logger.warning(f"Không tìm thấy phân tích để xóa: {analysis_id}")