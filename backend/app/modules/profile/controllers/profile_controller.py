from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, List, Dict, Any, Optional
import logging
import uuid
from fastapi import UploadFile # Nhớ import thêm UploadFile

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.profile.schemas.user_profile_schemas import (
    UserProfileUpdate, UserProfileResponse, ProfileStatisticsResponse,AvatarUploadResponse
)
from app.modules.profile.services.profile_service import ProfileService
from app.utils.constants import error_codes as ErrorCode, messages as Message

logger = logging.getLogger(__name__)


class ProfileController:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_service = ProfileService(db)

    def _handle_http_exception(self, e: HTTPException, user_id: Optional[uuid.UUID] = None) -> ErrorResponse:
        """Handle HTTPException and return appropriate ErrorResponse"""
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
        """Create internal server error response"""
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
            
            logger.info(f"[UPDATE_PROFILE] Success: {user_id}")
            return SuccessResponse(message=Message.PROFILE_UPDATE_SUCCESS_MSG, data=profile_response)
        except HTTPException as e:
            logger.error(f"[UPDATE_PROFILE] HTTPException: {e.detail}")
            return self._handle_http_exception(e, user_id)
        except Exception as e:
            logger.error(f"[UPDATE_PROFILE] Error: {e}", exc_info=True)
            return self._internal_error(Message.INTERNAL_ERROR_MSG, ErrorCode.INTERNAL_ERROR, e)

    async def get_profile(self, user_id: uuid.UUID) -> Union[SuccessResponse[UserProfileResponse], ErrorResponse]:
        """Lấy thông tin hồ sơ"""
        try:
            logger.info(f"[GET_PROFILE] {user_id}")
            profile = await self.profile_service.get_profile_by_user_id(user_id)

            if not profile:
                logger.warning(f"[GET_PROFILE] Not found: {user_id}")
                return ErrorResponse(
                    message=Message.PROFILE_NOT_FOUND_MSG, error_code=ErrorCode.PROFILE_NOT_FOUND,
                    error_details={"user_id": str(user_id)}, status_code=status.HTTP_404_NOT_FOUND
                )

            profile_response = await self.profile_service.create_profile_response(profile)
            logger.info(f"[GET_PROFILE] Success: {user_id}")
            return SuccessResponse(message=Message.PROFILE_GET_SUCCESS_MSG, data=profile_response)
        except Exception as e:
            logger.error(f"[GET_PROFILE] Error: {e}", exc_info=True)
            return self._internal_error(Message.PROFILE_GET_ERROR_MSG, ErrorCode.PROFILE_GET_ERROR, e)

    async def get_profile_by_str_id(self, user_id: str) -> Union[SuccessResponse[UserProfileResponse], ErrorResponse]:
        """Lấy hồ sơ theo string ID (convert to UUID)"""
        try:
            logger.info(f"[GET_PROFILE_STR] {user_id}")
            
            # Convert to UUID
            try:
                uuid_user_id = uuid.UUID(user_id)
            except ValueError:
                logger.warning(f"[GET_PROFILE_STR] Invalid UUID: {user_id}")
                return ErrorResponse(
                    message=Message.USER_INVALID_DATA_MSG, error_code=ErrorCode.USER_INVALID_DATA,
                    error_details={"user_id": user_id, "error": "Invalid UUID format"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Reuse get_profile logic
            return await self.get_profile(uuid_user_id)
        except Exception as e:
            logger.error(f"[GET_PROFILE_STR] Error: {e}", exc_info=True)
            return self._internal_error(Message.INTERNAL_ERROR_MSG, ErrorCode.INTERNAL_ERROR, e)

    async def get_profile_statistics(self) -> Union[SuccessResponse[ProfileStatisticsResponse], ErrorResponse]:
        """Lấy thống kê hồ sơ"""
        try:
            logger.info("[STATISTICS] Fetching profile stats")
            stats = await self.profile_service.get_profile_statistics()
            
            total = stats.total_profiles if hasattr(stats, 'total_profiles') else 'N/A'
            logger.info(f"[STATISTICS] Success - Total: {total}")
            return SuccessResponse(message=Message.PROFILE_STATISTICS_SUCCESS_MSG, data=stats)
        except Exception as e:
            logger.error(f"[STATISTICS] Error: {e}", exc_info=True)
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

            # Use list comprehension instead of loop
            profile_responses = [
                await self.profile_service.create_profile_response(p) for p in profiles
            ]

            logger.info(f"[SEARCH] Success: {len(profile_responses)} profiles")
            return SuccessResponse(
                message=Message.PROFILE_SEARCH_FOUND_COUNT_MSG.format(count=len(profile_responses)),
                data=profile_responses
            )
        except Exception as e:
            logger.error(f"[SEARCH] Error: {e}", exc_info=True)
            return self._internal_error(Message.PROFILE_SEARCH_ERROR_MSG, ErrorCode.PROFILE_SEARCH_ERROR, e)

    async def get_profile_completion_suggestions(self, user_id: uuid.UUID) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Lấy gợi ý hoàn thiện hồ sơ"""
        try:
            logger.info(f"[COMPLETION] {user_id}")
            suggestions = await self.profile_service.get_profile_completion_suggestions(user_id)
            
            completion = suggestions.get('completion_percentage', 0)
            logger.info(f"[COMPLETION] Success: {user_id} - {completion}%")
            return SuccessResponse(message=Message.PROFILE_COMPLETION_SUGGESTIONS_SUCCESS_MSG, data=suggestions)
        except HTTPException as e:
            logger.error(f"[COMPLETION] HTTPException: {e.detail}")
            return self._handle_http_exception(e, user_id)
        except Exception as e:
            logger.error(f"[COMPLETION] Error: {e}", exc_info=True)
            return self._internal_error(Message.PROFILE_COMPLETION_SUGGESTIONS_ERROR_MSG, ErrorCode.PROFILE_COMPLETION_SUGGESTIONS_ERROR, e)
        
    async def upload_avatar(self, file: UploadFile) -> Union[SuccessResponse[AvatarUploadResponse], ErrorResponse]:
        """Upload avatar và trả về URL"""
        try:
            logger.info(f"[UPLOAD_AVATAR] Filename: {file.filename}")
            
            # Gọi service để lưu file
            avatar_url = await self.profile_service.save_avatar_file(file)
            
            data = AvatarUploadResponse(url=avatar_url)
            
            logger.info(f"[UPLOAD_AVATAR] Success: {avatar_url}")
            return SuccessResponse(
                message="Upload ảnh thành công", 
                data=data
            )
            
        except HTTPException as e:
            logger.error(f"[UPLOAD_AVATAR] HTTPException: {e.detail}")
            # Tái sử dụng hàm handle lỗi có sẵn
            return self._handle_http_exception(e)
        except Exception as e:
            logger.error(f"[UPLOAD_AVATAR] Error: {e}", exc_info=True)
            return self._internal_error("Lỗi upload ảnh", ErrorCode.INTERNAL_ERROR, e)