from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, Dict, Any, Optional
from fastapi import UploadFile
import logging

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.upload.schemas.upload import ImageUploadResponse, WoundImageDetail
from app.modules.upload.services.upload_service import UploadService
from app.utils.exceptions.base_exceptions import AppBaseException
from app.utils.constants.error_codes import *

logger = logging.getLogger(__name__)

class UploadController:
    def __init__(self, db: AsyncSession) -> None:
        self.upload_service: UploadService = UploadService(db)
    
    async def upload_image(
        self, 
        user_id: str, 
        file: UploadFile,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:

        try:
            result = await self.upload_service.handle_image_upload(
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
            result = await self.upload_service.get_image_by_id(image_id, user_id)

            if result["success"]:
                wound_image = result["data"]
                wound_detail = WoundImageDetail(
                    id=wound_image.id,
                    user_id=wound_image.user_id,
                    file_name=wound_image.file_name,
                    file_path=wound_image.file_path,
                    file_size=wound_image.file_size,
                    file_type=wound_image.file_type,
                    width=wound_image.width,
                    height=wound_image.height,
                    upload_status=wound_image.upload_status,
                    wound_type=wound_image.wound_type,
                    confidence_score=wound_image.confidence_score,
                    severity=wound_image.severity,
                    ai_model_version=wound_image.ai_model_version,
                    processing_time_ms=wound_image.processing_time_ms,
                    error_message=wound_image.error_message,
                    created_at=wound_image.created_at,
                    updated_at=wound_image.updated_at,
                    processed_at=wound_image.processed_at
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
            result = await self.upload_service.get_user_images(user_id, limit, offset)

            if result["success"]:
                images_data = []
                for wound_image in result["data"]:
                    image_detail = WoundImageDetail(
                        id=wound_image.id,
                        user_id=wound_image.user_id,
                        file_name=wound_image.file_name,
                        file_path=wound_image.file_path,
                        file_size=wound_image.file_size,
                        file_type=wound_image.file_type,
                        width=wound_image.width,
                        height=wound_image.height,
                        upload_status=wound_image.upload_status,
                        wound_type=wound_image.wound_type,
                        confidence_score=wound_image.confidence_score,
                        severity=wound_image.severity,
                        ai_model_version=wound_image.ai_model_version,
                        processing_time_ms=wound_image.processing_time_ms,
                        error_message=wound_image.error_message,
                        created_at=wound_image.created_at,
                        updated_at=wound_image.updated_at,
                        processed_at=wound_image.processed_at
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