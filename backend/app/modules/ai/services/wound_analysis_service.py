from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from typing import Dict, Any, List, Optional, Tuple
import logging
import os
import uuid
from datetime import datetime

from app.modules.ai.models.wound_analysis import WoundAnalysis
from app.modules.ai.models.wound_detection import WoundDetection
from app.modules.ai.services.detection_processor import DetectionProcessor
from app.modules.firstaid.services.first_aid_service import FirstAidService

logger = logging.getLogger(__name__)


class WoundAnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.first_aid_service = FirstAidService(db)
        self.processor = DetectionProcessor

    async def get_first_aid_guide_for_detection(
        self,
        detection: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Lấy first aid guide phù hợp cho một detection.
        """
        original_wound_type = detection.get("wound_type", "unknown")
        detection_severity = detection.get("severity", "mild")

        # Map wound type
        mapped_wound_type = self.processor.map_wound_type_for_database(original_wound_type)

        # Special handling for burn
        if original_wound_type.lower() == "burn":
            return await self._get_burn_guide(original_wound_type, detection_severity)

        # Other wound types
        logger.info(
            f"Getting guide for {original_wound_type}/{detection_severity} "
            f"(mapped: {mapped_wound_type})"
        )

        return await self.first_aid_service.get_first_aid_guide(
            wound_type=mapped_wound_type,
            severity=detection_severity
        )

    async def _get_burn_guide(
        self,
        wound_type: str,
        severity: str
    ) -> Optional[Dict[str, Any]]:
        """
        Lấy burn guide với sub-type support.
        """
        base_type, parsed_severity, sub_type = self.processor.parse_burn_classification(
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
    def extract_guide_id(guide: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract firstaidguide_id from guide."""
        if not guide:
            return None
        return guide.get("firstaidguide_id")

    @staticmethod
    def extract_snapshot(guide: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract snapshot data from guide."""
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
        user_id: str,
        image_url: str,
        file_name: str,
        file_size: int,
        ai_model_version: str,
        processing_time_ms: int,
        total_detections: int = 0
    ) -> WoundAnalysis:
        """
        Tạo analysis record cho trường hợp không có vết thương.
        """
        analysis = WoundAnalysis.create_analysis(
            user_id=user_id,
            image_url=image_url,
            file_name=file_name,
            file_size=file_size,
            ai_model_version=ai_model_version,
            total_detections=total_detections,
            processing_time_ms=processing_time_ms,
            primary_wound_type="not_wound",
            primary_severity="mild",
            primary_firstaidguide_id=None,
            firstaid_snapshot={
                "title": "Không phát hiện vết thương",
                "description": (
                    "Không có vết thương được phát hiện trong hình ảnh"
                    if total_detections == 0
                    else "Không có vết thương đạt ngưỡng độ tin cậy"
                ),
                "steps": [],
                "warnings": [],
                "dos": [],
                "donts": []
            }
        )

        self.db.add(analysis)
        await self.db.commit()

        if not analysis.analysis_id:
            logger.error("Analysis ID not generated after commit")
            raise Exception("Failed to generate analysis ID")

        logger.info(f"Created no-wound analysis successfully: {analysis.analysis_id}")

        logger.info(f"Created no-wound analysis: {analysis.analysis_id}")
        return analysis

    async def create_wound_analysis(
        self,
        user_id: str,
        image_url: str,
        file_name: str,
        file_size: int,
        ai_model_version: str,
        total_detections: int,
        processing_time_ms: int,
        primary_detection: Dict[str, Any],
        first_aid_guide: Optional[Dict[str, Any]]
    ) -> WoundAnalysis:
        """
        Tạo analysis record cho trường hợp có vết thương.
        """
        # Extract guide info
        guide_id = self.extract_guide_id(first_aid_guide)
        snapshot = self.extract_snapshot(first_aid_guide)

        # Map wound type và severity
        original_wound_type = primary_detection.get("wound_type", "unknown")
        mapped_wound_type = self.processor.map_wound_type_for_database(original_wound_type)
        parsed_severity = self.processor.get_parsed_severity_for_storage(
            original_wound_type,
            primary_detection.get("severity", "mild")
        )

        # Create analysis
        analysis = WoundAnalysis.create_analysis(
            user_id=user_id,
            image_url=image_url,
            file_name=file_name,
            file_size=file_size,
            ai_model_version=ai_model_version,
            total_detections=total_detections,
            processing_time_ms=processing_time_ms,
            primary_wound_type=mapped_wound_type,
            primary_severity=parsed_severity,
            primary_firstaidguide_id=guide_id,
            firstaid_snapshot=snapshot
        )

        self.db.add(analysis)
        await self.db.commit()

        # Ensure analysis_id is available after commit
        if not analysis.analysis_id:
            logger.error("Analysis ID not generated after commit")
            raise Exception("Failed to generate analysis ID")

        logger.info(f"Created analysis successfully: {analysis.analysis_id}")
        
        return analysis
    async def save_detections(
        self,
        analysis_id: str,
        detections: List[Dict[str, Any]],
        primary_guide_id: Optional[str] = None
    ) -> None:
        """
        Lưu wound detections vào database.
        """
        for detection in detections:
            original_wound_type = detection.get("wound_type", "unknown")
            mapped_wound_type = self.processor.map_wound_type_for_database(
                original_wound_type
            )

            guide_id = primary_guide_id if detection.get("is_primary") else None

            parsed_severity = self.processor.get_parsed_severity_for_storage(
                original_wound_type,
                detection.get("severity", "mild")
            )

            wound_detection = WoundDetection.create_detection(
                analysis_id=analysis_id,
                wound_type=mapped_wound_type,
                severity=parsed_severity,
                confidence_score=detection.get("confidence", 0.0),
                bounding_box=detection.get("bounding_box", {}),
                detection_index=detection.get("detection_index", 0),
                is_primary=detection.get("is_primary", False),
                firstaidguide_id=guide_id
            )
            self.db.add(wound_detection)

        await self.db.commit()
        logger.info(f"Saved {len(detections)} detections for analysis {analysis_id}")

    async def get_user_analysis_history(self, user_id: str) -> List[WoundAnalysis]:
        """
        Lấy lịch sử phân tích của user.
        """
        query = select(WoundAnalysis).options(
            selectinload(WoundAnalysis.wound_detections)
        ).where(
            WoundAnalysis.user_id == user_id,
            WoundAnalysis.is_deleted == False
        ).order_by(WoundAnalysis.created_at.desc())

        result = await self.db.execute(query)
        return result.scalars().all()