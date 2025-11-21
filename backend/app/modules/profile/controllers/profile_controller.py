from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, List, Dict, Any, Optional
from fastapi import status
import logging
import uuid

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.profile.schemas.user_profile_schemas import (
    UserProfileUpdate,
    UserProfileResponse,
    ProfileStatisticsResponse
)
from app.modules.profile.services.profile_service import ProfileService
from app.utils.exceptions.base_exceptions import AppBaseException

# Import constants
from app.utils.constants import error_codes as ErrorCode
from app.utils.constants import messages as Message

logger = logging.getLogger(__name__)


class ProfileController:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_service = ProfileService(db)

    async def update_profile(
        self,
        user_id: uuid.UUID,
        profile_data: UserProfileUpdate
    ) -> Union[SuccessResponse[UserProfileResponse], ErrorResponse]:
        """
        Cập nhật thông tin hồ sơ người dùng.

        Args:
            user_id: ID người dùng
            profile_data: Dữ liệu hồ sơ cần cập nhật

        Returns:
            SuccessResponse với dữ liệu hồ sơ hoặc ErrorResponse
        """
        try:
            logger.info(f"[CẬP_NHẬT_HỒ_SƠ] Đang cập nhật hồ sơ cho người dùng: {user_id}")
            
            updated_profile = await self.profile_service.update_profile(
                user_id, profile_data
            )

            profile_response = await self.profile_service.create_profile_response(
                updated_profile
            )

            logger.info(f"[CẬP_NHẬT_HỒ_SƠ] Thành công: {user_id}")
            
            return SuccessResponse(
                message=Message.PROFILE_UPDATE_SUCCESS_MSG,
                data=profile_response
            )

        except AppBaseException as e:
            logger.error(f"[CẬP_NHẬT_HỒ_SƠ] AppBaseException: {e.message}")
            
            if e.error_code == ErrorCode.USER_NOT_FOUND:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"user_id": str(user_id)},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            elif e.error_code == ErrorCode.USER_INVALID_DATA:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"validation_error": str(e)},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            else:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code or ErrorCode.UNKNOWN_ERROR,
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"[CẬP_NHẬT_HỒ_SƠ] Lỗi không mong muốn: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_profile(
        self,
        user_id: uuid.UUID
    ) -> Union[SuccessResponse[UserProfileResponse], ErrorResponse]:
        """Lấy thông tin hồ sơ người dùng."""
        try:
            logger.info(f"[LẤY_HỒ_SƠ] Đang lấy hồ sơ cho người dùng: {user_id}")
            
            profile = await self.profile_service.get_profile_by_user_id(user_id)

            if not profile:
                logger.warning(f"[LẤY_HỒ_SƠ] Không tìm thấy hồ sơ: {user_id}")
                return ErrorResponse(
                    message=Message.PROFILE_NOT_FOUND_MSG,
                    error_code=ErrorCode.PROFILE_NOT_FOUND,
                    error_details={"user_id": str(user_id)},
                    status_code=status.HTTP_404_NOT_FOUND
                )

            profile_response = await self.profile_service.create_profile_response(
                profile
            )

            logger.info(f"[LẤY_HỒ_SƠ] Thành công: {user_id}")
            
            return SuccessResponse(
                message=Message.PROFILE_GET_SUCCESS_MSG,
                data=profile_response
            )

        except Exception as e:
            logger.error(f"[LẤY_HỒ_SƠ] Lỗi không mong muốn: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.PROFILE_GET_ERROR_MSG,
                error_code=ErrorCode.PROFILE_GET_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_profile_by_str_id(
        self,
        user_id: str
    ) -> Union[SuccessResponse[UserProfileResponse], ErrorResponse]:
        """Lấy hồ sơ người dùng theo ID người dùng dạng chuỗi (chuyển đổi thành UUID)."""
        try:
            logger.info(f"[LẤY_HỒ_SƠ_STR] Đang lấy hồ sơ cho người dùng: {user_id}")
            
            # Convert string to UUID
            try:
                uuid_user_id = uuid.UUID(user_id)
            except ValueError:
                logger.warning(f"[LẤY_HỒ_SƠ_STR] Định dạng UUID không hợp lệ: {user_id}")
                return ErrorResponse(
                    message=Message.USER_INVALID_DATA_MSG,
                    error_code=ErrorCode.USER_INVALID_DATA,
                    error_details={"user_id": user_id, "error": "Invalid UUID format"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            profile = await self.profile_service.get_profile_by_user_id(uuid_user_id)

            if not profile:
                logger.warning(f"[LẤY_HỒ_SƠ_STR] Không tìm thấy hồ sơ: {user_id}")
                return ErrorResponse(
                    message=Message.PROFILE_NOT_FOUND_MSG,
                    error_code=ErrorCode.PROFILE_NOT_FOUND,
                    error_details={"user_id": user_id},
                    status_code=status.HTTP_404_NOT_FOUND
                )

            profile_response = await self.profile_service.create_profile_response(
                profile
            )

            logger.info(f"[LẤY_HỒ_SƠ_STR] Thành công: {user_id}")
            
            return SuccessResponse(
                message=Message.PROFILE_GET_SUCCESS_MSG,
                data=profile_response
            )

        except Exception as e:
            logger.error(f"[LẤY_HỒ_SƠ_STR] Lỗi không mong muốn: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_profile_statistics(
        self
    ) -> Union[SuccessResponse[ProfileStatisticsResponse], ErrorResponse]:
        """Lấy thống kê về hồ sơ người dùng."""
        try:
            logger.info("[THỐNG_KÊ] Đang lấy thống kê hồ sơ")
            
            stats = await self.profile_service.get_profile_statistics()

            logger.info(
                f"[THỐNG_KÊ] Thành công - Tổng hồ sơ: {stats.total_profiles if hasattr(stats, 'total_profiles') else 'N/A'}"
            )
            
            return SuccessResponse(
                message=Message.PROFILE_STATISTICS_SUCCESS_MSG,
                data=stats
            )

        except Exception as e:
            logger.error(f"[THỐNG_KÊ] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.PROFILE_STATISTICS_ERROR_MSG,
                error_code=ErrorCode.PROFILE_STATISTICS_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def search_profiles(
        self,
        full_name: Optional[str] = None,
        gender: Optional[str] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Union[SuccessResponse[List[UserProfileResponse]], ErrorResponse]:
        """Tìm kiếm hồ sơ với bộ lọc."""
        try:
            logger.info(
                f"[TÌM_KIẾM_HỒ_SƠ] Đang tìm kiếm - tên: {full_name}, "
                f"giới tính: {gender}, tuổi: {min_age}-{max_age}, "
                f"giới hạn: {limit}, offset: {offset}"
            )
            
            profiles = await self.profile_service.search_profiles(
                full_name=full_name,
                gender=gender,
                min_age=min_age,
                max_age=max_age,
                limit=limit,
                offset=offset
            )

            profile_responses = []
            for profile in profiles:
                profile_response = await self.profile_service.create_profile_response(
                    profile
                )
                profile_responses.append(profile_response)

            logger.info(
                f"[TÌM_KIẾM_HỒ_SƠ] Thành công: tìm thấy {len(profile_responses)} hồ sơ"
            )
            
            return SuccessResponse(
                message=Message.PROFILE_SEARCH_FOUND_COUNT_MSG.format(
                    count=len(profile_responses)
                ),
                data=profile_responses
            )

        except Exception as e:
            logger.error(f"[TÌM_KIẾM_HỒ_SƠ] Lỗi: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.PROFILE_SEARCH_ERROR_MSG,
                error_code=ErrorCode.PROFILE_SEARCH_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_profile_completion_suggestions(
        self,
        user_id: uuid.UUID
    ) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Lấy gợi ý để hoàn thiện hồ sơ."""
        try:
            logger.info(
                f"[GỢI_Ý_HOÀN_THIỆN] Đang lấy gợi ý cho người dùng: {user_id}"
            )
            
            suggestions = await self.profile_service.get_profile_completion_suggestions(
                user_id
            )

            logger.info(
                f"[GỢI_Ý_HOÀN_THIỆN] Thành công: {user_id} - "
                f"Hoàn thiện: {suggestions.get('completion_percentage', 0)}%"
            )
            
            return SuccessResponse(
                message=Message.PROFILE_COMPLETION_SUGGESTIONS_SUCCESS_MSG,
                data=suggestions
            )

        except AppBaseException as e:
            logger.error(
                f"[GỢI_Ý_HOÀN_THIỆN] AppBaseException: {e.message}"
            )
            
            if e.error_code == ErrorCode.USER_NOT_FOUND:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"user_id": str(user_id)},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            elif e.error_code == ErrorCode.PROFILE_NOT_FOUND:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"user_id": str(user_id)},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            else:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code or ErrorCode.UNKNOWN_ERROR,
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(
                f"[GỢI_Ý_HOÀN_THIỆN] Lỗi không mong muốn: {e}",
                exc_info=True
            )
            return ErrorResponse(
                message=Message.PROFILE_COMPLETION_SUGGESTIONS_ERROR_MSG,
                error_code=ErrorCode.PROFILE_COMPLETION_SUGGESTIONS_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )