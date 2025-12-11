from typing import Dict, Any, Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status, HTTPException
import logging
import uuid

from app.modules.firstaid.services.first_aid_service import FirstAidService
from app.modules.firstaid.schemas.first_aid_schemas import FirstAidGuideResponse, WoundTypeResponse
from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.utils.constants import error_codes as ErrorCode, messages as Message

logger = logging.getLogger(__name__)


class FirstAidController:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.first_aid_service = FirstAidService(db)
        self._severity_map = {"mild": "Nhẹ", "moderate": "Trung bình", "severe": "Nặng"}

    def _format_message(self, base_msg: str, wound_type: str, severity: str, sub_type: Optional[str] = None) -> str:
        """Định dạng tin nhắn với sub_type tùy chọn"""
        msg = base_msg.format(wound_type=wound_type, severity=severity)
        return f"{msg} với sub_type '{sub_type}'" if sub_type else msg

    def _count_items(self, data: Optional[Union[List, Dict]]) -> int:
        """Đếm số lượng item trong list hoặc dict với key 'items'"""
        if not data:
            return 0
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            return len(data.get("items", []))
        return 0

    def _extract_source_dict(self, source_data: Optional[Union[str, Dict]]) -> Optional[Dict[str, Any]]:
        """Trích xuất dict nguồn từ đối tượng JSONB hoặc chuyển chuỗi thành dict"""
        if not source_data:
            return None
        if isinstance(source_data, str):
            return {"name": source_data}
        if isinstance(source_data, dict):
            # JSONB format: {"name": "...", "url": "..."}
            return source_data
        return None

    def _create_guide_response(self, guide: Dict[str, Any], expected_wound_type: str, expected_severity: str) -> FirstAidGuideResponse:
        """Tạo FirstAidGuideResponse từ dữ liệu hướng dẫn"""
        return FirstAidGuideResponse(
            firstaidguide_id=uuid.UUID(guide.get("firstaidguide_id", "00000000-0000-0000-0000-000000000000")),
            wound_type=guide.get("wound_type", expected_wound_type),
            severity=guide.get("severity", expected_severity),
            sub_type=guide.get("sub_type"),
            severity_display=self._severity_map.get(guide.get("severity", expected_severity).lower(), guide.get("severity", expected_severity)),
            title=guide.get("title", ""),
            steps=guide.get("steps"),
            dos=guide.get("dos"),
            donts=guide.get("donts"),
            supplies_needed=guide.get("supplies_needed"),
            estimated_healing_time=guide.get("estimated_healing_time"),
            source=self._extract_source_dict(guide.get("source")),
            is_active=guide.get("is_active", True),
            version=guide.get("version", 1),
            created_by=uuid.UUID(guide["created_by"]) if guide.get("created_by") else None,
            created_at=guide.get("created_at"),
            updated_at=guide.get("updated_at"),
            has_complete_instructions=bool(guide.get("dos") and guide.get("donts")),
            instructions_count=self._count_items(guide.get("steps")),
            supplies_count=self._count_items(guide.get("supplies_needed"))
        )

    async def _get_available_combinations(self) -> List[str]:
        """Lấy các kết hợp wound_type/severity có sẵn"""
        try:
            wound_types = await self.first_aid_service.get_available_wound_types()
            return [f"{wt['wound_type']}/{sev}" for wt in wound_types for sev in wt.get("severities", [])]
        except Exception as e:
            logger.warning(f"[COMBINATIONS] Lỗi: {e}")
            return []

    async def get_first_aid_guide(self, wound_type: str, severity: str, sub_type: Optional[str] = None) -> Union[SuccessResponse[FirstAidGuideResponse], ErrorResponse]:
        """Lấy hướng dẫn sơ cứu cho loại và mức độ vết thương cụ thể"""
        try:
            logger.info(f"[FIRSTAID_GUIDE] {wound_type}/{severity}, loại phụ: {sub_type}")
            guide = await self.first_aid_service.get_first_aid_guide(wound_type, severity, sub_type)

            if not guide:
                logger.warning(f"[FIRSTAID_GUIDE] Không tìm thấy: {wound_type}/{severity}")
                error_msg = Message.FIRSTAID_GUIDE_NOT_FOUND_WITH_SUBTYPE_MSG if sub_type else Message.FIRSTAID_GUIDE_NOT_FOUND_FOR_MSG
                
                return ErrorResponse(
                    message=self._format_message(error_msg, wound_type, severity, sub_type),
                    error_code=ErrorCode.FIRSTAID_GUIDE_NOT_FOUND,
                    error_details={
                        "wound_type": wound_type, "severity": severity, "sub_type": sub_type,
                        "available_types": await self._get_available_combinations()
                    },
                    status_code=status.HTTP_404_NOT_FOUND
                )

            guide_response = self._create_guide_response(guide, wound_type, severity)
            logger.info(f"[FIRSTAID_GUIDE] Thành công: {guide.get('firstaidguide_id')}")
            
            return SuccessResponse(
                message=self._format_message(Message.FIRSTAID_GUIDE_FOUND_FOR_MSG, wound_type, severity, sub_type),
                data=guide_response
            )
        except HTTPException as e:
            logger.warning(f"[FIRSTAID_GUIDE] Lỗi HTTP: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"[FIRSTAID_GUIDE] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.FIRSTAID_GUIDE_ERROR_MSG, error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_available_wound_types(self) -> Union[SuccessResponse[List[WoundTypeResponse]], ErrorResponse]:
        """Lấy tất cả các loại vết thương có sẵn"""
        try:
            logger.info("[WOUND_TYPES] Đang lấy các loại vết thương có sẵn")
            wound_types = await self.first_aid_service.get_available_wound_types()
            wound_type_responses = [WoundTypeResponse(**wt) for wt in wound_types]
            
            logger.info(f"[WOUND_TYPES] Thành công: {len(wound_type_responses)} loại")
            return SuccessResponse(message=Message.WOUND_TYPES_SUCCESS_MSG, data=wound_type_responses)
        except HTTPException as e:
            logger.warning(f"[WOUND_TYPES] Lỗi HTTP: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.WOUND_TYPES_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"[WOUND_TYPES] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.WOUND_TYPES_ERROR_MSG, error_code=ErrorCode.WOUND_TYPES_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def search_first_aid_guides(self, wound_type: Optional[str] = None, severity: Optional[str] = None,
                                     limit: int = 20, offset: int = 0, is_active: Optional[bool] = None, 
                                     search: Optional[str] = None) -> Union[SuccessResponse[List[FirstAidGuideResponse]], ErrorResponse]:
        """Tìm kiếm hướng dẫn sơ cứu với bộ lọc"""
        try:
            logger.info(f"[SEARCH_GUIDES] loại vết thương: {wound_type}, mức độ: {severity}, giới hạn: {limit}, vị trí bắt đầu: {offset}, đang hoạt động: {is_active}, tìm kiếm: {search}")
            result = await self.first_aid_service.search_first_aid_guides(
                wound_type, severity, limit, offset, is_active, search
            )
            
            # Service returns {"items": [...], "total": N}
            guides = result.get("items", [])
            total_count = result.get("total", 0)
            
            guide_responses = [
                self._create_guide_response(g, g.get("wound_type", ""), g.get("severity", ""))
                for g in guides
            ]
            
            logger.info(f"[SEARCH_GUIDES] Thành công: {len(guide_responses)} hướng dẫn (Tổng: {total_count})")
            return SuccessResponse(
                message=Message.FIRSTAID_GUIDES_FOUND_COUNT_MSG.format(count=len(guide_responses)),
                data=guide_responses,
                total=total_count
            )
        except HTTPException as e:
            logger.warning(f"[SEARCH_GUIDES] Lỗi HTTP: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_SEARCH_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"[SEARCH_GUIDES] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.FIRSTAID_SEARCH_ERROR_MSG, error_code=ErrorCode.FIRSTAID_SEARCH_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_statistics(self) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Lấy thống kê về cơ sở kiến thức sơ cứu"""
        try:
            logger.info("[STATISTICS] Đang lấy thống kê")
            stats = await self.first_aid_service.get_guide_statistics()
            
            logger.info(f"[STATISTICS] Thành công - Tổng hướng dẫn: {stats.get('total_guides', 0)}")
            return SuccessResponse(message=Message.FIRSTAID_STATISTICS_SUCCESS_MSG, data=stats)
        except HTTPException as e:
            logger.warning(f"[STATISTICS] Lỗi HTTP: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_STATISTICS_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"[STATISTICS] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.FIRSTAID_STATISTICS_ERROR_MSG, error_code=ErrorCode.FIRSTAID_STATISTICS_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def validate_guide_availability(self, wound_type: str, severity: str, 
                                         sub_type: Optional[str] = None) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Kiểm tra tính khả dụng của hướng dẫn sơ cứu"""
        try:
            logger.info(f"[VALIDATE] {wound_type}/{severity}, loại phụ: {sub_type}")
            guide = await self.first_aid_service.get_first_aid_guide(wound_type, severity, sub_type)

            if guide:
                success_msg = Message.FIRSTAID_GUIDE_AVAILABLE_WITH_SUBTYPE_MSG if sub_type else Message.FIRSTAID_GUIDE_AVAILABLE_FOR_MSG
                logger.info(f"[VALIDATE] Có sẵn: {guide.get('firstaidguide_id')}")
                
                return SuccessResponse(
                    message=self._format_message(success_msg, wound_type, severity, sub_type),
                    data={
                        "available": True,
                        "guide_id": guide.get("firstaidguide_id"),
                        "sub_type": guide.get("sub_type"),
                        "version": guide.get("version"),
                        "last_updated": guide.get("updated_at")
                    }
                )
            else:
                # Get alternatives
                available_types = await self.first_aid_service.get_available_wound_types()
                alternatives = [
                    f"{wt['wound_type']}/{sev}"
                    for wt in available_types
                    for sev in wt.get("severities", [])
                    if not (wt["wound_type"] == wound_type and sev == severity)
                ]
                
                not_avail_msg = Message.FIRSTAID_GUIDE_NOT_AVAILABLE_WITH_SUBTYPE_MSG if sub_type else Message.FIRSTAID_GUIDE_NOT_AVAILABLE_FOR_MSG
                logger.info(f"[VALIDATE] Không có sẵn, {len(alternatives)} lựa chọn thay thế")
                
                return SuccessResponse(
                    message=self._format_message(not_avail_msg, wound_type, severity, sub_type),
                    data={
                        "available": False,
                        "alternatives": alternatives[:5],
                        "total_alternatives": len(alternatives)
                    }
                )
        except HTTPException as e:
            logger.warning(f"[VALIDATE] Lỗi HTTP: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_VALIDATION_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"[VALIDATE] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.FIRSTAID_VALIDATION_ERROR_MSG, error_code=ErrorCode.FIRSTAID_VALIDATION_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_first_aid_guide(self, guide_data: Dict[str, Any], current_user_id: uuid.UUID) -> Union[SuccessResponse[FirstAidGuideResponse], ErrorResponse]:
        """Tạo hướng dẫn sơ cứu mới (Chỉ Admin)"""
        try:
            logger.info(f"[CREATE_GUIDE] Đang tạo hướng dẫn cho {guide_data.get('wound_type')}/{guide_data.get('severity')}")
            
            guide = await self.first_aid_service.create_first_aid_guide(guide_data, current_user_id)
            
            if not guide:
                return ErrorResponse(
                    message="Không thể tạo hướng dẫn sơ cứu",
                    error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            guide_response = self._create_guide_response(guide, guide.get("wound_type", ""), guide.get("severity", ""))
            logger.info(f"[CREATE_GUIDE] Thành công: {guide.get('firstaidguide_id')}")
            
            return SuccessResponse(
                message="Tạo hướng dẫn sơ cứu thành công",
                data=guide_response
            )
        except HTTPException as e:
            logger.warning(f"[CREATE_GUIDE] Lỗi HTTP: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except ValueError as e:
            logger.warning(f"[CREATE_GUIDE] Lỗi xác thực: {e}")
            error_msg = str(e)
            
            # Check if it's a duplicate error
            is_duplicate = "already exists" in error_msg.lower()
            
            # Enhance the error message for duplicates
            if is_duplicate:
                message = f"Hướng dẫn bị trùng lặp: {error_msg}"
                error_code = "FIRSTAID_GUIDE_DUPLICATE"
                suggestion = "Bạn có thể chỉnh sửa hướng dẫn hiện có hoặc đặt 'is_active' thành false để tạo phiên bản không hoạt động"
            else:
                message = error_msg
                error_code = ErrorCode.FIRSTAID_GUIDE_ERROR
                suggestion = None
            
            return ErrorResponse(
                message=message,
                error_code=error_code,
                error_details={
                    "duplicate": is_duplicate,
                    "suggestion": suggestion
                } if is_duplicate else None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"[CREATE_GUIDE] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message="Lỗi khi tạo hướng dẫn sơ cứu",
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_guide_by_id(self, guide_id: uuid.UUID) -> Union[SuccessResponse[FirstAidGuideResponse], ErrorResponse]:
        """Lấy hướng dẫn sơ cứu theo ID"""
        try:
            logger.info(f"[GET_GUIDE] Đang lấy hướng dẫn {guide_id}")
            
            guide = await self.first_aid_service.get_guide_by_id(guide_id)
            
            if not guide:
                return ErrorResponse(
                    message="Không tìm thấy hướng dẫn sơ cứu",
                    error_code=ErrorCode.FIRSTAID_GUIDE_NOT_FOUND,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            guide_response = self._create_guide_response(guide, guide.get("wound_type", ""), guide.get("severity", ""))
            logger.info(f"[GET_GUIDE] Thành công: {guide_id}")
            
            return SuccessResponse(
                message="Lấy hướng dẫn sơ cứu thành công",
                data=guide_response
            )
        except HTTPException as e:
            logger.warning(f"[GET_GUIDE] Lỗi HTTP: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"[GET_GUIDE] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message="Lỗi khi lấy hướng dẫn sơ cứu",
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update_first_aid_guide(self, guide_id: uuid.UUID, update_data: Dict[str, Any]) -> Union[SuccessResponse[FirstAidGuideResponse], ErrorResponse]:
        """Cập nhật hướng dẫn sơ cứu (Chỉ Admin)"""
        try:
            logger.info(f"[UPDATE_GUIDE] Đang cập nhật hướng dẫn {guide_id}")
            
            guide = await self.first_aid_service.update_first_aid_guide(guide_id, update_data)
            
            if not guide:
                return ErrorResponse(
                    message="Không tìm thấy hướng dẫn sơ cứu",
                    error_code=ErrorCode.FIRSTAID_GUIDE_NOT_FOUND,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            guide_response = self._create_guide_response(guide, guide.get("wound_type", ""), guide.get("severity", ""))
            logger.info(f"[UPDATE_GUIDE] Thành công: {guide_id}")
            
            return SuccessResponse(
                message="Cập nhật hướng dẫn sơ cứu thành công",
                data=guide_response
            )
        except HTTPException as e:
            logger.warning(f"[UPDATE_GUIDE] Lỗi HTTP: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except ValueError as e:
            logger.warning(f"[UPDATE_GUIDE] Lỗi xác thực: {e}")
            return ErrorResponse(
                message=str(e),
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"[UPDATE_GUIDE] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message="Lỗi khi cập nhật hướng dẫn sơ cứu",
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def delete_first_aid_guide(self, guide_id: uuid.UUID, hard_delete: bool = False) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Xóa hướng dẫn sơ cứu (Chỉ Admin)"""
        try:
            logger.info(f"[DELETE_GUIDE] Đang xóa hướng dẫn {guide_id} (xóa_vĩnh_viễn={hard_delete})")
            
            success = await self.first_aid_service.delete_first_aid_guide(guide_id, hard_delete)
            
            if not success:
                return ErrorResponse(
                    message="Không tìm thấy hướng dẫn sơ cứu",
                    error_code=ErrorCode.FIRSTAID_GUIDE_NOT_FOUND,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            delete_type = "vĩnh viễn" if hard_delete else "tạm thời"
            logger.info(f"[DELETE_GUIDE] Thành công: {guide_id} ({delete_type})")
            
            return SuccessResponse(
                message=f"Xóa hướng dẫn sơ cứu {delete_type} thành công",
                data={"guide_id": str(guide_id), "hard_delete": hard_delete}
            )
        except HTTPException as e:
            logger.warning(f"[DELETE_GUIDE] Lỗi HTTP: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"[DELETE_GUIDE] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message="Lỗi khi xóa hướng dẫn sơ cứu",
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
