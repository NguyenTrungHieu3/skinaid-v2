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
        """Format message with optional sub_type"""
        msg = base_msg.format(wound_type=wound_type, severity=severity)
        return f"{msg} với sub_type '{sub_type}'" if sub_type else msg

    def _count_items(self, data: Optional[Union[List, Dict]]) -> int:
        """Count items in list or dict with 'items' key"""
        if not data:
            return 0
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            return len(data.get("items", []))
        return 0

    def _extract_source_string(self, source_data: Optional[Union[str, Dict]]) -> Optional[str]:
        """Extract source string from JSONB object or return string as-is"""
        if not source_data:
            return None
        if isinstance(source_data, str):
            return source_data
        if isinstance(source_data, dict):
            # JSONB format: {"source": "...", "reference": "..."}
            return source_data.get("source")
        return None

    def _create_guide_response(self, guide: Dict[str, Any], expected_wound_type: str, expected_severity: str) -> FirstAidGuideResponse:
        """Create FirstAidGuideResponse from guide data"""
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
            source=self._extract_source_string(guide.get("source")),
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
        """Get available wound_type/severity combinations"""
        try:
            wound_types = await self.first_aid_service.get_available_wound_types()
            return [f"{wt['wound_type']}/{sev}" for wt in wound_types for sev in wt.get("severities", [])]
        except Exception as e:
            logger.warning(f"[COMBINATIONS] Error: {e}")
            return []

    async def get_first_aid_guide(self, wound_type: str, severity: str, sub_type: Optional[str] = None) -> Union[SuccessResponse[FirstAidGuideResponse], ErrorResponse]:
        """Get first aid guide for specific wound type and severity"""
        try:
            logger.info(f"[FIRSTAID_GUIDE] {wound_type}/{severity}, sub_type: {sub_type}")
            guide = await self.first_aid_service.get_first_aid_guide(wound_type, severity, sub_type)

            if not guide:
                logger.warning(f"[FIRSTAID_GUIDE] Not found: {wound_type}/{severity}")
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
            logger.info(f"[FIRSTAID_GUIDE] Success: {guide.get('firstaidguide_id')}")
            
            return SuccessResponse(
                message=self._format_message(Message.FIRSTAID_GUIDE_FOUND_FOR_MSG, wound_type, severity, sub_type),
                data=guide_response
            )
        except HTTPException as e:
            logger.warning(f"[FIRSTAID_GUIDE] HTTPException: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"[FIRSTAID_GUIDE] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.FIRSTAID_GUIDE_ERROR_MSG, error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_available_wound_types(self) -> Union[SuccessResponse[List[WoundTypeResponse]], ErrorResponse]:
        """Get all available wound types"""
        try:
            logger.info("[WOUND_TYPES] Fetching available wound types")
            wound_types = await self.first_aid_service.get_available_wound_types()
            wound_type_responses = [WoundTypeResponse(**wt) for wt in wound_types]
            
            logger.info(f"[WOUND_TYPES] Success: {len(wound_type_responses)} types")
            return SuccessResponse(message=Message.WOUND_TYPES_SUCCESS_MSG, data=wound_type_responses)
        except HTTPException as e:
            logger.warning(f"[WOUND_TYPES] HTTPException: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.WOUND_TYPES_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"[WOUND_TYPES] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.WOUND_TYPES_ERROR_MSG, error_code=ErrorCode.WOUND_TYPES_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def search_first_aid_guides(self, wound_type: Optional[str] = None, severity: Optional[str] = None,
                                     limit: int = 20, offset: int = 0, is_active: Optional[bool] = None, 
                                     search: Optional[str] = None) -> Union[SuccessResponse[List[FirstAidGuideResponse]], ErrorResponse]:
        """Search first aid guides with filters"""
        try:
            logger.info(f"[SEARCH_GUIDES] wound_type: {wound_type}, severity: {severity}, limit: {limit}, offset: {offset}, is_active: {is_active}, search: {search}")
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
            
            logger.info(f"[SEARCH_GUIDES] Success: {len(guide_responses)} guides (Total: {total_count})")
            return SuccessResponse(
                message=Message.FIRSTAID_GUIDES_FOUND_COUNT_MSG.format(count=len(guide_responses)),
                data=guide_responses,
                total=total_count
            )
        except HTTPException as e:
            logger.warning(f"[SEARCH_GUIDES] HTTPException: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_SEARCH_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"[SEARCH_GUIDES] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.FIRSTAID_SEARCH_ERROR_MSG, error_code=ErrorCode.FIRSTAID_SEARCH_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_statistics(self) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Get statistics about first aid knowledge base"""
        try:
            logger.info("[STATISTICS] Fetching statistics")
            stats = await self.first_aid_service.get_guide_statistics()
            
            logger.info(f"[STATISTICS] Success - Total guides: {stats.get('total_guides', 0)}")
            return SuccessResponse(message=Message.FIRSTAID_STATISTICS_SUCCESS_MSG, data=stats)
        except HTTPException as e:
            logger.warning(f"[STATISTICS] HTTPException: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_STATISTICS_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"[STATISTICS] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.FIRSTAID_STATISTICS_ERROR_MSG, error_code=ErrorCode.FIRSTAID_STATISTICS_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def validate_guide_availability(self, wound_type: str, severity: str, 
                                         sub_type: Optional[str] = None) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Check availability of first aid guide"""
        try:
            logger.info(f"[VALIDATE] {wound_type}/{severity}, sub_type: {sub_type}")
            guide = await self.first_aid_service.get_first_aid_guide(wound_type, severity, sub_type)

            if guide:
                success_msg = Message.FIRSTAID_GUIDE_AVAILABLE_WITH_SUBTYPE_MSG if sub_type else Message.FIRSTAID_GUIDE_AVAILABLE_FOR_MSG
                logger.info(f"[VALIDATE] Available: {guide.get('firstaidguide_id')}")
                
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
                logger.info(f"[VALIDATE] Not available, {len(alternatives)} alternatives")
                
                return SuccessResponse(
                    message=self._format_message(not_avail_msg, wound_type, severity, sub_type),
                    data={
                        "available": False,
                        "alternatives": alternatives[:5],
                        "total_alternatives": len(alternatives)
                    }
                )
        except HTTPException as e:
            logger.warning(f"[VALIDATE] HTTPException: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_VALIDATION_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"[VALIDATE] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.FIRSTAID_VALIDATION_ERROR_MSG, error_code=ErrorCode.FIRSTAID_VALIDATION_ERROR,
                error_details={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_first_aid_guide(self, guide_data: Dict[str, Any], current_user_id: uuid.UUID) -> Union[SuccessResponse[FirstAidGuideResponse], ErrorResponse]:
        """Create new first aid guide (Admin only)"""
        try:
            logger.info(f"[CREATE_GUIDE] Creating guide for {guide_data.get('wound_type')}/{guide_data.get('severity')}")
            
            guide = await self.first_aid_service.create_first_aid_guide(guide_data, current_user_id)
            
            if not guide:
                return ErrorResponse(
                    message="Failed to create first aid guide",
                    error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            guide_response = self._create_guide_response(guide, guide.get("wound_type", ""), guide.get("severity", ""))
            logger.info(f"[CREATE_GUIDE] Success: {guide.get('firstaidguide_id')}")
            
            return SuccessResponse(
                message="Tạo hướng dẫn sơ cứu thành công",
                data=guide_response
            )
        except HTTPException as e:
            logger.warning(f"[CREATE_GUIDE] HTTPException: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except ValueError as e:
            logger.warning(f"[CREATE_GUIDE] Validation error: {e}")
            error_msg = str(e)
            
            # Check if it's a duplicate error
            is_duplicate = "already exists" in error_msg.lower()
            
            # Enhance the error message for duplicates
            if is_duplicate:
                message = f"Duplicate guide: {error_msg}"
                error_code = "FIRSTAID_GUIDE_DUPLICATE"
                suggestion = "You can edit the existing guide or set 'is_active' to false to create an inactive version"
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
            logger.error(f"[CREATE_GUIDE] Error: {e}", exc_info=True)
            return ErrorResponse(
                message="Lỗi khi tạo hướng dẫn sơ cứu",
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_guide_by_id(self, guide_id: uuid.UUID) -> Union[SuccessResponse[FirstAidGuideResponse], ErrorResponse]:
        """Get first aid guide by ID"""
        try:
            logger.info(f"[GET_GUIDE] Getting guide {guide_id}")
            
            guide = await self.first_aid_service.get_guide_by_id(guide_id)
            
            if not guide:
                return ErrorResponse(
                    message="Không tìm thấy hướng dẫn sơ cứu",
                    error_code=ErrorCode.FIRSTAID_GUIDE_NOT_FOUND,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            guide_response = self._create_guide_response(guide, guide.get("wound_type", ""), guide.get("severity", ""))
            logger.info(f"[GET_GUIDE] Success: {guide_id}")
            
            return SuccessResponse(
                message="Lấy hướng dẫn sơ cứu thành công",
                data=guide_response
            )
        except HTTPException as e:
            logger.warning(f"[GET_GUIDE] HTTPException: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"[GET_GUIDE] Error: {e}", exc_info=True)
            return ErrorResponse(
                message="Lỗi khi lấy hướng dẫn sơ cứu",
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update_first_aid_guide(self, guide_id: uuid.UUID, update_data: Dict[str, Any]) -> Union[SuccessResponse[FirstAidGuideResponse], ErrorResponse]:
        """Update first aid guide (Admin only)"""
        try:
            logger.info(f"[UPDATE_GUIDE] Updating guide {guide_id}")
            
            guide = await self.first_aid_service.update_first_aid_guide(guide_id, update_data)
            
            if not guide:
                return ErrorResponse(
                    message="Không tìm thấy hướng dẫn sơ cứu",
                    error_code=ErrorCode.FIRSTAID_GUIDE_NOT_FOUND,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            guide_response = self._create_guide_response(guide, guide.get("wound_type", ""), guide.get("severity", ""))
            logger.info(f"[UPDATE_GUIDE] Success: {guide_id}")
            
            return SuccessResponse(
                message="Cập nhật hướng dẫn sơ cứu thành công",
                data=guide_response
            )
        except HTTPException as e:
            logger.warning(f"[UPDATE_GUIDE] HTTPException: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except ValueError as e:
            logger.warning(f"[UPDATE_GUIDE] Validation error: {e}")
            return ErrorResponse(
                message=str(e),
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"[UPDATE_GUIDE] Error: {e}", exc_info=True)
            return ErrorResponse(
                message="Lỗi khi cập nhật hướng dẫn sơ cứu",
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def delete_first_aid_guide(self, guide_id: uuid.UUID, hard_delete: bool = False) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Delete first aid guide (Admin only)"""
        try:
            logger.info(f"[DELETE_GUIDE] Deleting guide {guide_id} (hard_delete={hard_delete})")
            
            success = await self.first_aid_service.delete_first_aid_guide(guide_id, hard_delete)
            
            if not success:
                return ErrorResponse(
                    message="Không tìm thấy hướng dẫn sơ cứu",
                    error_code=ErrorCode.FIRSTAID_GUIDE_NOT_FOUND,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            delete_type = "vĩnh viễn" if hard_delete else "tạm thời"
            logger.info(f"[DELETE_GUIDE] Success: {guide_id} ({delete_type})")
            
            return SuccessResponse(
                message=f"Xóa hướng dẫn sơ cứu {delete_type} thành công",
                data={"guide_id": str(guide_id), "hard_delete": hard_delete}
            )
        except HTTPException as e:
            logger.warning(f"[DELETE_GUIDE] HTTPException: {e.detail}")
            return ErrorResponse(
                message=e.detail,
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"[DELETE_GUIDE] Error: {e}", exc_info=True)
            return ErrorResponse(
                message="Lỗi khi xóa hướng dẫn sơ cứu",
                error_code=ErrorCode.FIRSTAID_GUIDE_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
