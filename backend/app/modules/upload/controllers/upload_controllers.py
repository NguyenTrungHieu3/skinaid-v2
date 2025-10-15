from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, Dict, Any, Optional, List
from fastapi import UploadFile
import logging

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.upload.schemas.upload import ImageUploadResponse, WoundImageDetail
from app.modules.upload.schemas.validation import UploadValidationCreate, UploadValidationResponse
from app.modules.upload.models.wound_images import ImageInformation
from app.modules.upload.models.upload_validations import UploadValidation
from app.modules.upload.services.image_service import ImageService
from app.utils.exceptions.base_exceptions import AppBaseException
from app.utils.constants.error_codes import *

logger = logging.getLogger(__name__)

class UploadController:
    def __init__(self, db: AsyncSession) -> None:
        self.image_service: ImageService = ImageService(db)
    
    async def upload_image(
        self, 
        user_id: str, 
        file: UploadFile,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:

        try:
            result = await self.image_service.handle_image_upload_with_ai(
                user_id=user_id,
                file=file,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if result["success"]:
                return SuccessResponse(
                    message="Hình ảnh tải lên thành công",
                    data=result["data"]
                )
            else:
                return ErrorResponse(
                    message=result.get("error_message", "Upload failed"),
                    error_code=result.get("error_code", FILE_UPLOAD_FAILED),
                    error_details=None
                )
                
        except AppBaseException as e:
            return ErrorResponse(
                message=e.message,
                error_code=e.error_code or FILE_UPLOAD_FAILED,
                error_details=None
            )
        except Exception as e:
            logger.error(f"Unexpected error in upload_image: {str(e)}")
            return ErrorResponse(
                message="Có lỗi không mong muốn xảy ra trong quá trình tải lên",
                error_code=FILE_UPLOAD_FAILED,
                error_details=None
            )
    
    async def get_image_analysis(
        self, 
        image_id: str, 
        user_id: str
    ) -> Union[SuccessResponse[WoundImageDetail], ErrorResponse]:
        """Lấy kết quả phân tích hình ảnh vết thương."""
        try:
            result = await self.image_service.get_image_by_id(image_id, user_id)

            if result["success"]:
                image_information = result["data"]
                wound_detail = WoundImageDetail(
                    id=image_information.wound_images_id,
                    user_id=image_information.woundhistory_id,  # Using woundhistory_id as user_id for now
                    file_name=image_information.file_name,
                    file_path=image_information.file_path,
                    file_size=image_information.file_size,
                    file_type=image_information.file_type,
                    width=image_information.width,
                    height=image_information.height,
                    upload_status=image_information.upload_status,
                    error_message=image_information.error_message,
                    created_at=image_information.created_at,
                    updated_at=image_information.updated_at
                )

                return SuccessResponse(
                    message="Lấy phân tích hình ảnh thành công",
                    data=wound_detail
                )
            else:
                return ErrorResponse(
                    message=result.get("error_message", "Không tìm thấy hình ảnh"),
                    error_code=result.get("error_code", "IMAGE_NOT_FOUND"),
                    error_details=None
                )
                
        except AppBaseException as e:
            return ErrorResponse(
                message=e.message,
                error_code=e.error_code or "IMAGE_RETRIEVAL_FAILED",
                error_details=None
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_image_analysis: {str(e)}")
            return ErrorResponse(
                message="Có lỗi không mong muốn xảy ra khi lấy phân tích hình ảnh",
                error_code="IMAGE_RETRIEVAL_FAILED",
                error_details=None
            )
    
    async def get_user_images(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Lấy tất cả hình ảnh được tải lên bởi người dùng."""
        try:
            result = await self.image_service.get_user_images(user_id, limit, offset)

            if result["success"]:
                images_data = []
                for image_information in result["data"]:
                    image_detail = WoundImageDetail(
                        id=image_information.wound_images_id,
                        user_id=image_information.woundhistory_id,
                        file_name=image_information.file_name,
                        file_path=image_information.file_path,
                        file_size=image_information.file_size,
                        file_type=image_information.file_type,
                        width=image_information.width,
                        height=image_information.height,
                        upload_status=image_information.upload_status,
                        error_message=image_information.error_message,
                        created_at=image_information.created_at,
                        updated_at=image_information.updated_at
                    )
                    images_data.append(image_detail)

                return SuccessResponse(
                    message="Lấy hình ảnh người dùng thành công",
                    data={
                        "images": images_data,
                        "total": result.get("total", len(images_data)),
                        "limit": limit,
                        "offset": offset
                    }
                )
            else:
                return ErrorResponse(
                    message=result.get("error_message", "Không thể lấy hình ảnh"),
                    error_code=result.get("error_code", "IMAGES_RETRIEVAL_FAILED"),
                    error_details=None
                )
                
        except AppBaseException as e:
            return ErrorResponse(
                message=e.message,
                error_code=e.error_code or "IMAGES_RETRIEVAL_FAILED",
                error_details=None
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_user_images: {str(e)}")
            return ErrorResponse(
                message="Có lỗi không mong muốn xảy ra khi lấy hình ảnh người dùng",
                error_code="IMAGES_RETRIEVAL_FAILED",
                error_details=None
            )

    # ===== VALIDATION METHODS (Simplified) =====

    async def create_validation_record(
        self,
        validation_data: UploadValidationCreate,
        current_user,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> SuccessResponse[UploadValidationResponse]:
        """
        Tạo bản ghi validation mới (đơn giản hóa)
        """
        try:
            # Set user_id từ current_user nếu không được cung cấp
            if not validation_data.user_id:
                validation_data.user_id = current_user.user_id

            validation_record = await self.image_service.create_validation_record(
                validation_data=validation_data,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Tạo response đơn giản
            validation_response = UploadValidationResponse(
                upload_validations_id=validation_record.upload_validations_id,
                user_id=validation_record.user_id,
                file_name=validation_record.file_name,
                file_size=validation_record.file_size,
                file_type=validation_record.file_type,
                validation_passed=validation_record.validation_passed,
                validation_errors=validation_record.validation_errors,
                ip_address=validation_record.ip_address,
                user_agent=validation_record.user_agent,
                request_id=validation_record.request_id,
                attempt_count=validation_record.attempt_count,
                created_at=validation_record.created_at,
                updated_at=validation_record.updated_at
            )

            return SuccessResponse(
                message="Tạo bản ghi validation thành công",
                data=validation_response
            )

        except Exception as e:
            logger.error(f"Failed to create validation record: {e}")
            return ErrorResponse(
                message="Không thể tạo bản ghi validation",
                error_code="VALIDATION_CREATION_FAILED",
                error_details=None
            )

    async def get_user_validations(
        self,
        current_user,
        limit: int = 20,
        offset: int = 0
    ) -> SuccessResponse[List[UploadValidationResponse]]:
        """
        Lấy danh sách validation records của user hiện tại
        """
        try:
            validation_records = await self.image_service.get_user_validations(
                user_id=current_user.user_id,
                limit=limit,
                offset=offset
            )

            validation_responses = []
            for record in validation_records:
                response = UploadValidationResponse(
                    upload_validations_id=record.upload_validations_id,
                    user_id=record.user_id,
                    file_name=record.file_name,
                    file_size=record.file_size,
                    file_type=record.file_type,
                    validation_passed=record.validation_passed,
                    validation_errors=record.validation_errors,
                    ip_address=record.ip_address,
                    user_agent=record.user_agent,
                    request_id=record.request_id,
                    attempt_count=record.attempt_count,
                    created_at=record.created_at,
                    updated_at=record.updated_at
                )
                validation_responses.append(response)

            return SuccessResponse(
                message="Lấy danh sách validation thành công",
                data=validation_responses
            )

        except Exception as e:
            logger.error(f"Failed to get user validations for {current_user.user_id}: {e}")
            return ErrorResponse(
                message="Không thể lấy danh sách validation",
                error_code="VALIDATIONS_RETRIEVAL_FAILED",
                error_details=None
            )