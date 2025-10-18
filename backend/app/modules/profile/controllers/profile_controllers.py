from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, List, Dict, Any, Optional
import logging

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.profile.schemas.user_profile_schemas import UserProfileUpdate, UserProfileResponse, ProfileStatisticsResponse
from app.modules.profile.services.profile_service import ProfileService
from app.utils.exceptions.base_exceptions import AppBaseException
from app.utils.constants.error_codes import USER_INVALID_DATA, USER_NOT_FOUND

logger = logging.getLogger(__name__)

class ProfileController:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_service = ProfileService(db)

    async def update_profile(self, user_id: str, profile_data: UserProfileUpdate) -> Union[SuccessResponse[UserProfileResponse], ErrorResponse]:
        """
        Cập nhật thông tin profile của user.

        Args:
            user_id: ID của user
            profile_data: Dữ liệu profile cần cập nhật

        Returns:
            SuccessResponse với profile data hoặc ErrorResponse
        """
        try:
            updated_profile = await self.profile_service.update_profile(user_id, profile_data)

            profile_response = await self.profile_service.create_profile_response(updated_profile)

            return SuccessResponse(
                message="Cập nhật profile thành công",
                data=profile_response
            )

        except AppBaseException as e:
            if e.error_code == USER_NOT_FOUND:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"user_id": user_id}
                )
            elif e.error_code == USER_INVALID_DATA:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"validation_error": str(e)}
                )
            else:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code or "UNKNOWN_ERROR",
                    error_details=None
                )

        except Exception as e:
            logger.error(f"Unexpected error in update_profile: {str(e)}")
            return ErrorResponse(
                message="Có lỗi xảy ra, vui lòng thử lại",
                error_code="INTERNAL_ERROR",
                error_details=None
            )

    async def get_profile(self, user_id: str) -> Union[SuccessResponse[UserProfileResponse], ErrorResponse]:
        """Lấy thông tin profile của user."""
        try:
            profile = await self.profile_service.get_profile_by_user_id(user_id)

            if not profile:
                return ErrorResponse(
                    message="Profile không tồn tại",
                    error_code="PROFILE_NOT_FOUND",
                    error_details={"user_id": user_id}
                )

            profile_response = await self.profile_service.create_profile_response(profile)

            return SuccessResponse(
                message="Lấy profile thành công",
                data=profile_response
            )

        except Exception as e:
            logger.error(f"Unexpected error in get_profile: {str(e)}")
            return ErrorResponse(
                message="Có lỗi xảy ra khi lấy profile",
                error_code="INTERNAL_ERROR",
                error_details={"error": str(e)}
            )

    async def get_profile_statistics(self) -> SuccessResponse[ProfileStatisticsResponse]:
        """Lấy thống kê về user profiles."""
        try:
            stats = await self.profile_service.get_profile_statistics()

            return SuccessResponse(
                message="Lấy thống kê profile thành công",
                data=stats
            )

        except Exception as e:
            logger.error(f"Failed to get profile statistics: {e}")
            return ErrorResponse(
                message="Không thể lấy thống kê profile",
                error_code="STATISTICS_ERROR",
                error_details={"error": str(e)}
            )

    async def search_profiles(
        self,
        full_name: Optional[str] = None,
        gender: Optional[str] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> SuccessResponse[List[UserProfileResponse]]:
        """Tìm kiếm profiles với bộ lọc."""
        try:
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
                profile_response = await self.profile_service.create_profile_response(profile)
                profile_responses.append(profile_response)

            return SuccessResponse(
                message=f"Tìm thấy {len(profile_responses)} profiles",
                data=profile_responses
            )

        except Exception as e:
            logger.error(f"Failed to search profiles: {e}")
            return ErrorResponse(
                message="Không thể tìm kiếm profiles",
                error_code="SEARCH_ERROR",
                error_details={"error": str(e)}
            )

    async def get_profile_completion_suggestions(self, user_id: str) -> SuccessResponse[Dict[str, Any]]:
        """Lấy gợi ý hoàn thiện profile."""
        try:
            suggestions = await self.profile_service.get_profile_completion_suggestions(user_id)

            return SuccessResponse(
                message="Lấy gợi ý hoàn thiện profile thành công",
                data=suggestions
            )

        except Exception as e:
            logger.error(f"Failed to get completion suggestions for {user_id}: {e}")
            return ErrorResponse(
                message="Không thể lấy gợi ý hoàn thiện profile",
                error_code="COMPLETION_SUGGESTIONS_ERROR",
                error_details={"error": str(e)}
            )

        except AppBaseException as e:
            if e.error_code == USER_NOT_FOUND:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"user_id": user_id}
                )
            elif e.error_code == USER_INVALID_DATA:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code,
                    error_details={"validation_error": str(e)}
                )
            else:
                return ErrorResponse(
                    message=e.message,
                    error_code=e.error_code or "UNKNOWN_ERROR",
                    error_details=None
                )
        
        except Exception as e:
            logger.error(f"Unexpected error in update_profile: {str(e)}")
            return ErrorResponse(
                message="Có lỗi xảy ra, vui lòng thử lại",
                error_code="INTERNAL_ERROR",
                error_details=None
            )
    
    async def get_profile(self, user_id: str) -> Union[SuccessResponse[UserProfileResponse], ErrorResponse]:
        try:
            profile = await self.profile_service.get_profile_by_user_id(user_id)

            if not profile:
                return ErrorResponse(
                    message="Profile không tồn tại",
                    error_code="PROFILE_NOT_FOUND",
                    error_details={"user_id": user_id}
                )

            profile_response = await self.profile_service.create_profile_response(profile)

            return SuccessResponse(
                message="Lấy profile thành công",
                data=profile_response
            )

        except Exception as e:
            logger.error(f"Unexpected error in get_profile: {str(e)}")
            return ErrorResponse(
                message="Có lỗi xảy ra, vui lòng thử lại",
                error_code="INTERNAL_ERROR",
                error_details=None
            )