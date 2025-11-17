from typing import Dict, Any, Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
import logging
import uuid

from app.modules.firstaid.services.first_aid_service import FirstAidService
from app.modules.firstaid.schemas.first_aid_schemas import (
    FirstAidGuideResponse,
    WoundTypeResponse,
)
from app.shared.schemas.response import SuccessResponse, ErrorResponse

# Import constants
from app.utils.constants import error_codes as ErrorCode
from app.utils.constants import messages as Message

logger = logging.getLogger(__name__)


class FirstAidController:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.first_aid_service = FirstAidService(db)

    async def get_first_aid_guide(
        self,
        wound_type: str,
        severity: str,
        sub_type: Optional[str] = None,
    ) -> Union[SuccessResponse[FirstAidGuideResponse], ErrorResponse]:
        """Get first aid guide for specific wound type and severity."""
        try:
            logger.info(
                f"[FIRSTAID_GUIDE] Đang lấy hướng dẫn cho: {wound_type}/{severity}, sub_type: {sub_type}"
            )

            guide = await self.first_aid_service.get_first_aid_guide(
                wound_type, severity, sub_type
            )

            if not guide:
                logger.warning(
                    f"[FIRSTAID_GUIDE] Không tìm thấy: {wound_type}/{severity}, sub_type: {sub_type}"
                )

                # Format error message based on sub_type presence
                if sub_type:
                    error_message = (
                        Message.FIRSTAID_GUIDE_NOT_FOUND_WITH_SUBTYPE_MSG.format(
                            wound_type=wound_type,
                            severity=severity,
                            sub_type=sub_type,
                        )
                    )
                else:
                    error_message = Message.FIRSTAID_GUIDE_NOT_FOUND_FOR_MSG.format(
                        wound_type=wound_type,
                        severity=severity,
                    )

                available_combinations = await self._get_available_combinations()

                return ErrorResponse(
                    message=error_message,
                    error_code=ErrorCode.FIRSTAID_GUIDE_NOT_FOUND,
                    error_details={
                        "wound_type": wound_type,
                        "severity": severity,
                        "sub_type": sub_type,
                        "available_types": available_combinations,
                    },
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            guide_response = self._create_guide_response(
                guide, wound_type, severity
            )

            # Format success message based on sub_type presence
            if sub_type:
                success_message = (
                    f"{Message.FIRSTAID_GUIDE_FOUND_FOR_MSG.format(wound_type=wound_type, severity=severity)} với sub_type '{sub_type}'"
                )
            else:
                success_message = Message.FIRSTAID_GUIDE_FOUND_FOR_MSG.format(
                    wound_type=wound_type,
                    severity=severity,
                )

            logger.info(f"[FIRSTAID_GUIDE] Thành công: {guide.get('firstaidguide_id')}")

            return SuccessResponse(
                message=success_message,
                data=guide_response,
            )

        except Exception as e:
            logger.error(f"[FIRSTAID_GUIDE] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.FIRSTAID_GUIDE_ERROR_MSG,
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def get_available_wound_types(
        self,
    ) -> Union[SuccessResponse[List[WoundTypeResponse]], ErrorResponse]:
        """Get all available wound types."""
        try:
            logger.info("[WOUND_TYPES] Đang lấy các loại vết thương có sẵn")

            wound_types = await self.first_aid_service.get_available_wound_types()

            wound_type_responses = [
                WoundTypeResponse(**wt) for wt in wound_types
            ]

            logger.info(
                f"[WOUND_TYPES] Thành công: {len(wound_type_responses)} loại được tìm thấy"
            )

            return SuccessResponse(
                message=Message.WOUND_TYPES_SUCCESS_MSG,
                data=wound_type_responses,
            )

        except Exception as e:
            logger.error(f"[WOUND_TYPES] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.WOUND_TYPES_ERROR_MSG,
                error_code=ErrorCode.WOUND_TYPES_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def search_first_aid_guides(
        self,
        wound_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Union[SuccessResponse[List[FirstAidGuideResponse]], ErrorResponse]:
        """Search first aid guides with optional filters."""
        try:
            logger.info(
                f"[SEARCH_GUIDES] Đang tìm kiếm - wound_type: {wound_type}, "
                f"severity: {severity}, limit: {limit}, offset: {offset}"
            )

            guides = await self.first_aid_service.search_first_aid_guides(
                wound_type, severity, limit
            )

            guide_responses: List[FirstAidGuideResponse] = []
            for guide in guides:
                guide_response = self._create_guide_response(
                    guide,
                    guide.get("wound_type", ""),
                    guide.get("severity", ""),
                )
                guide_responses.append(guide_response)

            logger.info(
                f"[SEARCH_GUIDES] Thành công: {len(guide_responses)} hướng dẫn được tìm thấy"
            )

            return SuccessResponse(
                message=Message.FIRSTAID_GUIDES_FOUND_COUNT_MSG.format(
                    count=len(guide_responses)
                ),
                data=guide_responses,
            )

        except Exception as e:
            logger.error(f"[SEARCH_GUIDES] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.FIRSTAID_SEARCH_ERROR_MSG,
                error_code=ErrorCode.FIRSTAID_SEARCH_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def get_statistics(
        self,
    ) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Get statistics about first aid knowledge base."""
        try:
            logger.info("[STATISTICS] Đang lấy thống kê sơ cứu")

            stats = await self.first_aid_service.get_guide_statistics()

            logger.info(
                f"[STATISTICS] Thành công - Tổng số hướng dẫn: {stats.get('total_guides', 0)}"
            )

            return SuccessResponse(
                message=Message.FIRSTAID_STATISTICS_SUCCESS_MSG,
                data=stats,
            )

        except Exception as e:
            logger.error(f"[STATISTICS] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.FIRSTAID_STATISTICS_ERROR_MSG,
                error_code=ErrorCode.FIRSTAID_STATISTICS_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    async def validate_guide_availability(
        self,
        wound_type: str,
        severity: str,
        sub_type: Optional[str] = None,
    ) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Check availability of first aid guide."""
        try:
            logger.info(
                f"[VALIDATE] Đang kiểm tra tính khả dụng: {wound_type}/{severity}, "
                f"sub_type: {sub_type}"
            )

            guide = await self.first_aid_service.get_first_aid_guide(
                wound_type, severity, sub_type
            )

            if guide:
                # Format success message based on sub_type presence
                if sub_type:
                    success_message = (
                        Message.FIRSTAID_GUIDE_AVAILABLE_WITH_SUBTYPE_MSG.format(
                            wound_type=wound_type,
                            severity=severity,
                            sub_type=sub_type,
                        )
                    )
                else:
                    success_message = (
                        Message.FIRSTAID_GUIDE_AVAILABLE_FOR_MSG.format(
                            wound_type=wound_type,
                            severity=severity,
                        )
                    )

                logger.info(
                    f"[VALIDATE] Có sẵn: {guide.get('firstaidguide_id')}"
                )

                return SuccessResponse(
                    message=success_message,
                    data={
                        "available": True,
                        "guide_id": guide.get("firstaidguide_id"),
                        "sub_type": guide.get("sub_type"),
                        "version": guide.get("version"),
                        "last_updated": guide.get("updated_at"),
                    },
                )
            else:
                # Get alternatives
                available_types = (
                    await self.first_aid_service.get_available_wound_types()
                )
                alternatives: List[str] = []

                for wt in available_types:
                    for sev in wt.get("severities", []):
                        if not (
                            wt["wound_type"] == wound_type and sev == severity
                        ):
                            alternatives.append(f"{wt['wound_type']}/{sev}")

                # Format message based on sub_type presence
                if sub_type:
                    message = (
                        Message.FIRSTAID_GUIDE_NOT_AVAILABLE_WITH_SUBTYPE_MSG.format(
                            wound_type=wound_type,
                            severity=severity,
                            sub_type=sub_type,
                        )
                    )
                else:
                    message = (
                        Message.FIRSTAID_GUIDE_NOT_AVAILABLE_FOR_MSG.format(
                            wound_type=wound_type,
                            severity=severity,
                        )
                    )

                logger.info(
                    f"[VALIDATE] Không có sẵn: {wound_type}/{severity}, "
                    f"tìm thấy {len(alternatives)} lựa chọn thay thế"
                )

                return SuccessResponse(
                    message=message,
                    data={
                        "available": False,
                        "alternatives": alternatives[:5],
                        "total_alternatives": len(alternatives),
                    },
                )

        except Exception as e:
            logger.error(f"[VALIDATE] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.FIRSTAID_VALIDATION_ERROR_MSG,
                error_code=ErrorCode.FIRSTAID_VALIDATION_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ============================================
    # Private Helper Methods
    # ============================================

    def _get_severity_display(self, severity: str) -> str:
        """Convert severity to Vietnamese display name."""
        severity_map = {
            "mild": "Nhẹ",
            "moderate": "Trung bình",
            "severe": "Nặng",
        }
        return severity_map.get(severity.lower(), severity)

    def _count_instructions(self, steps: Optional[Dict[str, Any]]) -> int:
        """Count number of instruction steps."""
        if not steps:
            return 0
        if isinstance(steps, list):
            return len(steps)
        if isinstance(steps, dict):
            return len(steps.get("items", []))
        return 0

    def _count_supplies(self, supplies: Optional[Dict[str, Any]]) -> int:
        """Count number of supplies needed."""
        if not supplies:
            return 0
        if isinstance(supplies, list):
            return len(supplies)
        if isinstance(supplies, dict):
            return len(supplies.get("items", []))
        return 0

    def _create_guide_response(
        self,
        guide: Dict[str, Any],
        expected_wound_type: str,
        expected_severity: str,
    ) -> FirstAidGuideResponse:
        """Create FirstAidGuideResponse from guide data."""
        firstaidguide_id_str = guide.get("firstaidguide_id", "")
        created_by_str = guide.get("created_by")

        return FirstAidGuideResponse(
            firstaidguide_id=uuid.UUID(firstaidguide_id_str)
            if firstaidguide_id_str
            else uuid.UUID("00000000-0000-0000-0000-000000000000"),
            wound_type=guide.get("wound_type", expected_wound_type),
            severity=guide.get("severity", expected_severity),
            sub_type=guide.get("sub_type"),
            severity_display=self._get_severity_display(
                guide.get("severity", expected_severity)
            ),
            title=guide.get("title", ""),
            description=guide.get("description"),
            steps=guide.get("steps"),
            warnings=guide.get("warnings"),
            dos=guide.get("dos"),
            donts=guide.get("donts"),
            supplies_needed=guide.get("supplies_needed"),
            estimated_healing_time=guide.get("estimated_healing_time"),
            is_active=guide.get("is_active", True),
            version=guide.get("version", 1),
            created_by=uuid.UUID(created_by_str)
            if created_by_str
            else None,
            created_at=guide.get("created_at"),
            updated_at=guide.get("updated_at"),
            has_complete_instructions=bool(
                guide.get("dos") and guide.get("donts")
            ),
            instructions_count=self._count_instructions(guide.get("steps")),
            supplies_count=self._count_supplies(
                guide.get("supplies_needed")
            ),
        )

    async def _get_available_combinations(self) -> List[str]:
        """Get list of available wound_type/severity combinations."""
        try:
            wound_types = await self.first_aid_service.get_available_wound_types()
            combinations: List[str] = []
            for wt in wound_types:
                for severity in wt.get("severities", []):
                    combinations.append(f"{wt['wound_type']}/{severity}")
            return combinations
        except Exception as e:
            logger.warning(
                f"[COMBINATIONS] Không thể lấy các kết hợp: {e}"
            )
            return []
