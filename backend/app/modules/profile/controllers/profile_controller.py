from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, List, Dict, Any, Optional
import logging
import uuid
from fastapi import UploadFile # Nhớ import thêm UploadFile

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.profile.schemas.user_profile_schemas import (
    UserProfileUpdate, UserProfileResponse, ProfileStatisticsResponse,
    AvatarUploadResponse, AvatarDeleteResponse, PublicAvatarResponse
)
from app.modules.profile.services.profile_service import ProfileService
from app.utils.constants import error_codes as ErrorCode, messages as Message

logger = logging.getLogger(__name__)


class ProfileController:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_service = ProfileService(db)

    def _handle_http_exception(self, e: HTTPException, user_id: Optional[uuid.UUID] = None) -> ErrorResponse:
        """Xử lý HTTPException và trả về ErrorResponse phù hợp"""
        error_code = getattr(e, 'error_code', ErrorCode.UNKNOWN_ERROR)
        message = getattr(e, 'message', str(e.detail))
        
        status_map = {
            ErrorCode.USER_NOT_FOUND: status.HTTP_404_NOT_FOUND,
            ErrorCode.PROFILE_NOT_FOUND: status.HTTP_404_NOT_FOUND,
            ErrorCode.USER_INVALID_DATA: status.HTTP_400_BAD_REQUEST
        }
        
        return ErrorResponse(
            message=message,
            error_code=error_code,
            error_details={"user_id": str(user_id)} if user_id else {"error": str(e)},
            status_code=status_map.get(error_code, status.HTTP_400_BAD_REQUEST)
        )

    def _internal_error(self, message: str, error_code: str, error: Exception) -> ErrorResponse:
        """Tạo response lỗi nội bộ server"""
        return ErrorResponse(
            message=message, error_code=error_code,
            error_details={"error": str(error)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    async def update_profile(self, user_id: uuid.UUID, profile_data: UserProfileUpdate) -> Union[SuccessResponse[UserProfileResponse], ErrorResponse]:
        """Cập nhật thông tin hồ sơ"""
        try:
            logger.info(f"[UPDATE_PROFILE] {user_id}")
            updated_profile = await self.profile_service.update_profile(user_id, profile_data)
            profile_response = await self.profile_service.create_profile_response(updated_profile)
            
            logger.info(f"[UPDATE_PROFILE] Thành công: {user_id}")
            return SuccessResponse(message=Message.PROFILE_UPDATE_SUCCESS_MSG, data=profile_response)
        except HTTPException as e:
            logger.error(f"[UPDATE_PROFILE] HTTPException: {e.detail}")
            return self._handle_http_exception(e, user_id)
        except Exception as e:
            logger.error(f"[UPDATE_PROFILE] Lỗi: {e}", exc_info=True)
            return self._internal_error(Message.INTERNAL_ERROR_MSG, ErrorCode.INTERNAL_ERROR, e)

    async def get_profile(self, user_id: uuid.UUID) -> Union[SuccessResponse[UserProfileResponse], ErrorResponse]:
        """Lấy thông tin hồ sơ"""
        try:
            logger.info(f"[GET_PROFILE] {user_id}")
            profile = await self.profile_service.get_profile_by_user_id(user_id)

            if not profile:
                logger.warning(f"[GET_PROFILE] Không tìm thấy: {user_id}")
                return ErrorResponse(
                    message=Message.PROFILE_NOT_FOUND_MSG, error_code=ErrorCode.PROFILE_NOT_FOUND,
                    error_details={"user_id": str(user_id)}, status_code=status.HTTP_404_NOT_FOUND
                )

            profile_response = await self.profile_service.create_profile_response(profile)
            logger.info(f"[GET_PROFILE] Thành công: {user_id}")
            return SuccessResponse(message=Message.PROFILE_GET_SUCCESS_MSG, data=profile_response)
        except Exception as e:
            logger.error(f"[GET_PROFILE] Lỗi: {e}", exc_info=True)
            return self._internal_error(Message.PROFILE_GET_ERROR_MSG, ErrorCode.PROFILE_GET_ERROR, e)

    async def get_profile_by_str_id(self, user_id: str) -> Union[SuccessResponse[UserProfileResponse], ErrorResponse]:
        """Lấy hồ sơ theo string ID (chuyển đổi sang UUID)"""
        try:
            logger.info(f"[GET_PROFILE_STR] {user_id}")
            
            # Chuyển đổi sang UUID
            try:
                uuid_user_id = uuid.UUID(user_id)
            except ValueError:
                logger.warning(f"[GET_PROFILE_STR] UUID không hợp lệ: {user_id}")
                return ErrorResponse(
                    message=Message.USER_INVALID_DATA_MSG, error_code=ErrorCode.USER_INVALID_DATA,
                    error_details={"user_id": user_id, "error": "Định dạng UUID không hợp lệ"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Tái sử dụng logic get_profile
            return await self.get_profile(uuid_user_id)
        except Exception as e:
            logger.error(f"[GET_PROFILE_STR] Lỗi: {e}", exc_info=True)
            return self._internal_error(Message.INTERNAL_ERROR_MSG, ErrorCode.INTERNAL_ERROR, e)

    async def get_profile_statistics(self) -> Union[SuccessResponse[ProfileStatisticsResponse], ErrorResponse]:
        """Lấy thống kê hồ sơ"""
        try:
            logger.info("[STATISTICS] Đang lấy thống kê profile")
            stats = await self.profile_service.get_profile_statistics()
            
            total = stats.total_profiles if hasattr(stats, 'total_profiles') else 'N/A'
            logger.info(f"[STATISTICS] Thành công - Tổng: {total}")
            return SuccessResponse(message=Message.PROFILE_STATISTICS_SUCCESS_MSG, data=stats)
        except Exception as e:
            logger.error(f"[STATISTICS] Lỗi: {e}", exc_info=True)
            return self._internal_error(Message.PROFILE_STATISTICS_ERROR_MSG, ErrorCode.PROFILE_STATISTICS_ERROR, e)

    async def search_profiles(self, full_name: Optional[str] = None, gender: Optional[str] = None,
                             min_age: Optional[int] = None, max_age: Optional[int] = None,
                             limit: int = 20, offset: int = 0) -> Union[SuccessResponse[List[UserProfileResponse]], ErrorResponse]:
        """Tìm kiếm hồ sơ với bộ lọc"""
        try:
            logger.info(f"[SEARCH] name: {full_name}, gender: {gender}, age: {min_age}-{max_age}")
            
            profiles = await self.profile_service.search_profiles(
                full_name=full_name, gender=gender, min_age=min_age, max_age=max_age, limit=limit, offset=offset
            )

            # Sử dụng list comprehension thay vì vòng lặp
            profile_responses = [
                await self.profile_service.create_profile_response(p) for p in profiles
            ]

            logger.info(f"[SEARCH] Thành công: {len(profile_responses)} profiles")
            return SuccessResponse(
                message=Message.PROFILE_SEARCH_FOUND_COUNT_MSG.format(count=len(profile_responses)),
                data=profile_responses
            )
        except Exception as e:
            logger.error(f"[SEARCH] Lỗi: {e}", exc_info=True)
            return self._internal_error(Message.PROFILE_SEARCH_ERROR_MSG, ErrorCode.PROFILE_SEARCH_ERROR, e)

    async def get_profile_completion_suggestions(self, user_id: uuid.UUID) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Lấy gợi ý hoàn thiện hồ sơ"""
        try:
            logger.info(f"[COMPLETION] {user_id}")
            suggestions = await self.profile_service.get_profile_completion_suggestions(user_id)
            
            completion = suggestions.get('completion_percentage', 0)
            logger.info(f"[COMPLETION] Thành công: {user_id} - {completion}%")
            return SuccessResponse(message=Message.PROFILE_COMPLETION_SUGGESTIONS_SUCCESS_MSG, data=suggestions)
        except HTTPException as e:
            logger.error(f"[COMPLETION] HTTPException: {e.detail}")
            return self._handle_http_exception(e, user_id)
        except Exception as e:
            logger.error(f"[COMPLETION] Lỗi: {e}", exc_info=True)
            return self._internal_error(Message.PROFILE_COMPLETION_SUGGESTIONS_ERROR_MSG, ErrorCode.PROFILE_COMPLETION_SUGGESTIONS_ERROR, e)

    async def upload_avatar(
        self,
        user_id: uuid.UUID,
        file: UploadFile
    ) -> Union[SuccessResponse, ErrorResponse]:
        """
        Controller method để xử lý upload avatar request.

        Workflow:
        1. Ủy quyền logic sang ProfileService
        2. Xử lý exceptions và chuyển đổi thành ErrorResponse
        3. Gói kết quả vào SuccessResponse
        4. Log tất cả các thao tác để kiểm toán
        """
        logger.info(
            f"[CONTROLLER] Upload avatar request - "
            f"user: {user_id}, file: {file.filename}"
        )

        try:
            result = await self.profile_service.upload_avatar(
                user_id=user_id,
                file=file
            )

            logger.info(
                f"[CONTROLLER] Upload avatar thành công - "
                f"user: {user_id}, url: {result['avatar_url']}"
            )

            return SuccessResponse(
                message=Message.FILE_UPLOAD_SUCCESS_MSG,
                data=AvatarUploadResponse(**result),
                status_code=status.HTTP_200_OK
            )

        except HTTPException as e:
            logger.warning(
                f"[CONTROLLER] Upload avatar thất bại (HTTPException) - "
                f"user: {user_id}, lỗi: {e.detail}"
            )

            return self._handle_http_exception(e, user_id)

        except Exception as e:
            logger.error(
                f"[CONTROLLER] Upload avatar thất bại (Exception) - "
                f"user: {user_id}",
                exc_info=True
            )

            return self._internal_error(
                message="Lỗi khi upload avatar",
                error_code=ErrorCode.INTERNAL_ERROR,
                error=e
            )


    async def delete_avatar(
        self,
        user_id: uuid.UUID
    ) -> Union[SuccessResponse, ErrorResponse]:
        """
        Controller method để xử lý xóa avatar request.

        Workflow:
        1. Ủy quyền logic sang ProfileService
        2. Xử lý exceptions
        3. Trả về SuccessResponse hoặc ErrorResponse
        4. Log các thao tác
        """
        logger.info(f"[CONTROLLER] Delete avatar request - user: {user_id}")

        try:
            result = await self.profile_service.delete_avatar(user_id)

            logger.info(f"[CONTROLLER] Xóa avatar thành công - user: {user_id}")

            return SuccessResponse(
                message=Message.FILE_DELETE_SUCCESS_MSG,
                data=AvatarDeleteResponse(**result),
                status_code=status.HTTP_200_OK
            )

        except HTTPException as e:
            logger.warning(
                f"[CONTROLLER] Xóa avatar thất bại (HTTPException) - "
                f"user: {user_id}, lỗi: {e.detail}"
            )
            return self._handle_http_exception(e, user_id)

        except Exception as e:
            logger.error(
                f"[CONTROLLER] Xóa avatar thất bại (Exception) - user: {user_id}",
                exc_info=True
            )
            return self._internal_error(
                message="Lỗi khi xóa avatar",
                error_code=ErrorCode.INTERNAL_ERROR,
                error=e
            )


    async def get_public_avatar(
        self,
        user_id: uuid.UUID
    ) -> Union[SuccessResponse, ErrorResponse]:
        """
        Controller method để lấy avatar (public endpoint)
        """
        logger.debug(f"[CONTROLLER] Get public avatar - user: {user_id}")

        try:
            result = await self.profile_service.get_public_avatar(user_id)

            logger.debug(
                f"[CONTROLLER] Lấy public avatar thành công - "
                f"user: {user_id}, has_avatar: {result['has_avatar']}"
            )

            return SuccessResponse(
                message="Lấy thông tin avatar thành công",
                data=PublicAvatarResponse(**result),
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(
                f"[CONTROLLER] Lấy public avatar thất bại - user: {user_id}",
                exc_info=True
            )

            return SuccessResponse(
                message="Không thể lấy thông tin avatar",
                data=PublicAvatarResponse(
                    user_id=user_id,
                    avatar_url=None,
                    has_avatar=False
                ),
                status_code=status.HTTP_200_OK
            )
