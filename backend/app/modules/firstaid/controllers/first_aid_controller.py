from typing import Dict, Any, Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.firstaid.services.first_aid_service import FirstAidService
from app.modules.firstaid.schemas.first_aid_schemas import FirstAidGuideResponse, WoundTypeResponse
from app.shared.schemas.response import SuccessResponse, ErrorResponse
import logging
import uuid

logger = logging.getLogger(__name__)

class FirstAidController:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.first_aid_service = FirstAidService(db)

    async def get_first_aid_guide(
        self,
        wound_type: str,
        severity: str,
        sub_type: Optional[str] = None
    ) -> Union[SuccessResponse[FirstAidGuideResponse], ErrorResponse]:

        try:
            guide = await self.first_aid_service.get_first_aid_guide(wound_type, severity, sub_type)

            if not guide:
                sub_type_info = f" với sub_type '{sub_type}'" if sub_type else ""
                return ErrorResponse(
                    message=f"Không tìm thấy hướng dẫn sơ cứu cho vết thương loại '{wound_type}' mức độ '{severity}'{sub_type_info}",
                    error_code="FIRSTAID_GUIDE_NOT_FOUND",
                    error_details={
                        "wound_type": wound_type,
                        "severity": severity,
                        "sub_type": sub_type,
                        "available_types": await self._get_available_combinations()
                    }
                )

            guide_response = self._create_guide_response(guide, wound_type, severity)

            sub_type_display = f" với sub_type '{sub_type}'" if sub_type else ""
            return SuccessResponse(
                message=f"Lấy hướng dẫn sơ cứu thành công cho {wound_type}/{severity}{sub_type_display}",
                data=guide_response
            )

        except Exception as e:
            logger.error(f"Failed to get first aid guide: {e}")
            return ErrorResponse(
                message="Không thể lấy hướng dẫn sơ cứu",
                error_code="FIRSTAID_GUIDE_ERROR",
                error_details={"error": str(e)}
            )

    async def get_available_wound_types(self) -> SuccessResponse[List[WoundTypeResponse]]:
        try:
            wound_types = await self.first_aid_service.get_available_wound_types()

            wound_type_responses = [
                WoundTypeResponse(**wt) for wt in wound_types
            ]

            return SuccessResponse(
                message="Lấy danh sách loại vết thương thành công",
                data=wound_type_responses
            )

        except Exception as e:
            logger.error(f"Failed to get available wound types: {e}")
            return ErrorResponse(
                message="Không thể lấy loại vết thương",
                error_code="WOUND_TYPES_ERROR",
                error_details={"error": str(e)}
            )

    async def search_first_aid_guides(
        self,
        wound_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> SuccessResponse[List[FirstAidGuideResponse]]:

        try:
            guides = await self.first_aid_service.search_first_aid_guides(wound_type, severity, limit)

            guide_responses = []
            for guide in guides:
                guide_response = self._create_guide_response(guide, guide.get("wound_type", ""), guide.get("severity", ""))
                guide_responses.append(guide_response)

            return SuccessResponse(
                message=f"Tìm thấy {len(guide_responses)} hướng dẫn sơ cứu",
                data=guide_responses
            )

        except Exception as e:
            logger.error(f"Failed to search first aid guides: {e}")
            return ErrorResponse(
                message="Không thể tìm kiếm hướng dẫn sơ cứu",
                error_code="FIRSTAID_SEARCH_ERROR",
                error_details={"error": str(e)}
            )

    def _get_severity_display(self, severity: str) -> str:
        """Chuyển đổi severity sang tiếng Việt."""
        severity_map = {
            "mild": "Nhẹ",
            "moderate": "Trung bình",
            "severe": "Nặng"
        }
        return severity_map.get(severity.lower(), severity)

    def _count_instructions(self, steps: Optional[Dict[str, Any]]) -> int:
        """Đếm số bước hướng dẫn."""
        if not steps:
            return 0
        if isinstance(steps, list):
            return len(steps)
        elif isinstance(steps, dict):
            return len(steps.get('items', []))
        return 0

    def _count_supplies(self, supplies: Optional[Dict[str, Any]]) -> int:
        """Đếm số vật dụng cần thiết."""
        if not supplies:
            return 0
        if isinstance(supplies, list):
            return len(supplies)
        elif isinstance(supplies, dict):
            return len(supplies.get('items', []))
        return 0

    def _create_guide_response(self, guide: Dict[str, Any], expected_wound_type: str, expected_severity: str) -> FirstAidGuideResponse:
        """Tạo FirstAidGuideResponse từ guide data (DRY principle)."""
        firstaidguide_id_str = guide.get("firstaidguide_id", "")
        created_by_str = guide.get("created_by")

        return FirstAidGuideResponse(
            firstaidguide_id=uuid.UUID(firstaidguide_id_str) if firstaidguide_id_str else uuid.UUID("00000000-0000-0000-0000-000000000000"),
            wound_type=guide.get("wound_type", expected_wound_type),
            severity=guide.get("severity", expected_severity),
            sub_type=guide.get("sub_type"),
            severity_display=self._get_severity_display(guide.get("severity", expected_severity)),
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
            created_by=uuid.UUID(created_by_str) if created_by_str else None,
            created_at=guide.get("created_at"),
            updated_at=guide.get("updated_at"),
            has_complete_instructions=bool(guide.get("dos") and guide.get("donts")),
            instructions_count=self._count_instructions(guide.get("steps")),
            supplies_count=self._count_supplies(guide.get("supplies_needed"))
        )

    async def _get_available_combinations(self) -> List[str]:
        """Lấy danh sách các combination wound_type/severity có sẵn."""
        try:
            wound_types = await self.first_aid_service.get_available_wound_types()
            combinations = []
            for wt in wound_types:
                for severity in wt.get("severities", []):
                    combinations.append(f"{wt['wound_type']}/{severity}")
            return combinations
        except Exception:
            return []

    async def get_statistics(self) -> SuccessResponse[Dict[str, Any]]:
        """Lấy thống kê về first aid knowledge base."""
        try:
            stats = await self.first_aid_service.get_guide_statistics()

            return SuccessResponse(
                message="Lấy thống kê first aid thành công",
                data=stats
            )

        except Exception as e:
            logger.error(f"Failed to get first aid statistics: {e}")
            return ErrorResponse(
                message="Không thể lấy thống kê first aid",
                error_code="FIRSTAID_STATISTICS_ERROR",
                error_details={"error": str(e)}
            )

    async def validate_guide_availability(
        self,
        wound_type: str,
        severity: str,
        sub_type: Optional[str] = None
    ) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Kiểm tra tính khả dụng của first aid guide."""
        try:
            guide = await self.first_aid_service.get_first_aid_guide(wound_type, severity, sub_type)

            if guide:
                sub_type_info = f" với sub_type '{sub_type}'" if sub_type else ""
                return SuccessResponse(
                    message=f"Hướng dẫn sơ cứu cho {wound_type}/{severity}{sub_type_info} khả dụng",
                    data={
                        "available": True,
                        "guide_id": guide.get("firstaidguide_id"),
                        "sub_type": guide.get("sub_type"),
                        "version": guide.get("version"),
                        "last_updated": guide.get("updated_at")
                    }
                )
            else:
                available_types = await self.first_aid_service.get_available_wound_types()
                alternatives = []

                for wt in available_types:
                    for sev in wt.get("severities", []):
                        if not (wt["wound_type"] == wound_type and sev == severity):
                            alternatives.append(f"{wt['wound_type']}/{sev}")

                sub_type_info = f" với sub_type '{sub_type}'" if sub_type else ""
                return SuccessResponse(
                    message=f"Hướng dẫn sơ cứu cho {wound_type}/{severity}{sub_type_info} không khả dụng",
                    data={
                        "available": False,
                        "alternatives": alternatives[:5],
                        "total_alternatives": len(alternatives)
                    }
                )

        except Exception as e:
            logger.error(f"Failed to validate guide availability: {e}")
            return ErrorResponse(
                message="Không thể kiểm tra tính khả dụng của hướng dẫn",
                error_code="FIRSTAID_VALIDATION_ERROR",
                error_details={"error": str(e)}
            )

    async def create_first_aid_guide(
        self,
        guide_data: Dict[str, Any],
        current_user_id: uuid.UUID
    ) -> Union[SuccessResponse[FirstAidGuideResponse], ErrorResponse]:
        """Tạo hướng dẫn sơ cứu mới."""
        try:
            # Check if guide already exists
            existing = await self.first_aid_service.get_first_aid_guide(
                guide_data["wound_type"],
                guide_data["severity"],
                guide_data.get("sub_type")
            )
            
            if existing:
                sub_type_info = f" với sub_type '{guide_data.get('sub_type')}'" if guide_data.get("sub_type") else ""
                return ErrorResponse(
                    message=f"Hướng dẫn cho {guide_data['wound_type']}/{guide_data['severity']}{sub_type_info} đã tồn tại",
                    error_code="FIRSTAID_ALREADY_EXISTS",
                    error_details={"existing_guide_id": existing.get("firstaidguide_id")}
                )

            # Create new guide
            guide = await self.first_aid_service.create_first_aid_guide(
                guide_data,
                created_by=current_user_id
            )

            guide_response = self._create_guide_response(
                guide,
                guide_data["wound_type"],
                guide_data["severity"]
            )

            return SuccessResponse(
                message="Tạo hướng dẫn sơ cứu thành công",
                data=guide_response
            )

        except ValueError as ve:
            logger.error(f"Validation error creating guide: {ve}")
            return ErrorResponse(
                message="Dữ liệu không hợp lệ",
                error_code="FIRSTAID_VALIDATION_ERROR",
                error_details={"error": str(ve)}
            )
        except Exception as e:
            logger.error(f"Failed to create first aid guide: {e}")
            return ErrorResponse(
                message="Không thể tạo hướng dẫn sơ cứu",
                error_code="FIRSTAID_CREATE_ERROR",
                error_details={"error": str(e)}
            )

    async def update_first_aid_guide(
        self,
        guide_id: uuid.UUID,
        update_data: Dict[str, Any]
    ) -> Union[SuccessResponse[FirstAidGuideResponse], ErrorResponse]:
        """Cập nhật hướng dẫn sơ cứu."""
        try:
            # Check if guide exists
            existing = await self.first_aid_service.get_guide_by_id(guide_id)
            if not existing:
                return ErrorResponse(
                    message=f"Không tìm thấy hướng dẫn với ID {guide_id}",
                    error_code="FIRSTAID_NOT_FOUND",
                    error_details={"guide_id": str(guide_id)}
                )

            # Update guide
            updated_guide = await self.first_aid_service.update_first_aid_guide(
                guide_id,
                update_data
            )

            if not updated_guide:
                return ErrorResponse(
                    message="Không thể cập nhật hướng dẫn",
                    error_code="FIRSTAID_UPDATE_FAILED"
                )

            guide_response = self._create_guide_response(
                updated_guide,
                updated_guide["wound_type"],
                updated_guide["severity"]
            )

            return SuccessResponse(
                message="Cập nhật hướng dẫn sơ cứu thành công",
                data=guide_response
            )

        except Exception as e:
            logger.error(f"Failed to update first aid guide: {e}")
            return ErrorResponse(
                message="Không thể cập nhật hướng dẫn sơ cứu",
                error_code="FIRSTAID_UPDATE_ERROR",
                error_details={"error": str(e)}
            )

    async def delete_first_aid_guide(
        self,
        guide_id: uuid.UUID,
        hard_delete: bool = False
    ) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Xóa hướng dẫn sơ cứu."""
        try:
            # Check if guide exists
            existing = await self.first_aid_service.get_guide_by_id(guide_id)
            if not existing:
                return ErrorResponse(
                    message=f"Không tìm thấy hướng dẫn với ID {guide_id}",
                    error_code="FIRSTAID_NOT_FOUND",
                    error_details={"guide_id": str(guide_id)}
                )

            # Delete guide
            success = await self.first_aid_service.delete_first_aid_guide(
                guide_id,
                hard_delete=hard_delete
            )

            if not success:
                return ErrorResponse(
                    message="Không thể xóa hướng dẫn",
                    error_code="FIRSTAID_DELETE_FAILED"
                )

            delete_type = "vĩnh viễn" if hard_delete else "tạm thời"
            return SuccessResponse(
                message=f"Xóa hướng dẫn sơ cứu {delete_type} thành công",
                data={
                    "guide_id": str(guide_id),
                    "deleted_at": str(uuid.uuid4()),
                    "delete_type": "hard" if hard_delete else "soft"
                }
            )

        except Exception as e:
            logger.error(f"Failed to delete first aid guide: {e}")
            return ErrorResponse(
                message="Không thể xóa hướng dẫn sơ cứu",
                error_code="FIRSTAID_DELETE_ERROR",
                error_details={"error": str(e)}
            )

    async def get_guide_by_id(
        self,
        guide_id: uuid.UUID
    ) -> Union[SuccessResponse[FirstAidGuideResponse], ErrorResponse]:
        """Lấy hướng dẫn sơ cứu theo ID."""
        try:
            guide = await self.first_aid_service.get_guide_by_id(guide_id)
            
            if not guide:
                return ErrorResponse(
                    message=f"Không tìm thấy hướng dẫn với ID {guide_id}",
                    error_code="FIRSTAID_NOT_FOUND",
                    error_details={"guide_id": str(guide_id)}
                )

            guide_response = self._create_guide_response(
                guide,
                guide["wound_type"],
                guide["severity"]
            )

            return SuccessResponse(
                message="Lấy hướng dẫn sơ cứu thành công",
                data=guide_response
            )

        except Exception as e:
            logger.error(f"Failed to get guide by ID: {e}")
            return ErrorResponse(
                message="Không thể lấy hướng dẫn sơ cứu",
                error_code="FIRSTAID_GET_ERROR",
                error_details={"error": str(e)}
            )