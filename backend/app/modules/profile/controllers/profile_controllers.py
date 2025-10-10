from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union
import logging

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.profile.schemas.user_profile import UserProfileUpdate, UserProfileResponse
from app.modules.auth.services.auth_service import AuthService
from app.modules.profile.services.profile_service import ProfileService
from app.utils.exceptions.base_exceptions import AppBaseException
from app.utils.constants.error_codes import USER_INVALID_DATA, USER_NOT_FOUND

logger = logging.getLogger(__name__)

class ProfileController:  
    def __init__(self, db: AsyncSession):
        self.auth_service = AuthService(db)
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