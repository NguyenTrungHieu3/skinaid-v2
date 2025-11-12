import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Request

from app.modules.upload.services.upload_service import UploadService
from app.modules.upload.schemas.upload_schemas import UploadResponse, ValidationResult
from app.modules.audit.services.audit_service import AuditService
from app.shared.schemas.response import SuccessResponse

logger = logging.getLogger(__name__)


class UploadController:
    """Controller cho các thao tác upload."""
    
    # Constants
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditService(db)
        self.upload_service = UploadService(self.audit_service)
    
    async def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        mime_type: str,
        request: Request,
        user_id: Optional[str] = None,
        purpose: str = "general",
        quality: Optional[int] = None
    ) -> SuccessResponse[UploadResponse]:
        """
        Upload tệp với quy trình xác thực, xử lý và ghi log đầy đủ.

        Raises:
            HTTPException: Khi xảy ra lỗi xác thực hoặc lỗi xử lý.
        """
        try:
            # Kiểm tra giới hạn kích thước tệp phía controller (bảo vệ bổ sung)
            if len(file_content) > self.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File quá lớn (max 5MB)"
                )
            
            # Lấy thông tin client phục vụ audit/log
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            
            logger.info(f"[UPLOAD] Tệp {file_name} bởi {user_id or 'guest'}")

            # Gọi service xử lý upload
            result = await self.upload_service.upload_file(
                file_content=file_content,
                file_name=file_name,
                mime_type=mime_type,
                user_id=user_id,
                purpose=purpose,
                quality=quality,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Ánh xạ kết quả sang schema phản hồi
            response = UploadResponse(**result)
            
            logger.info(f"[UPLOAD] Thành công: {response.file_name}")
            
            return SuccessResponse(
                message="Upload thành công",
                data=response
            )
            
        except ValueError as e:
            logger.warning(f"[UPLOAD] Xác thực không hợp lệ: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
            
        except HTTPException:
            raise
            
        except Exception as e:
            logger.error(f"[UPLOAD] Lỗi không mong đợi: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Lỗi khi upload file"
            )
    
    async def validate_file(
        self,
        file_content: bytes,
        file_name: str,
        mime_type: str
    ) -> SuccessResponse[ValidationResult]:
        """
        Xác thực tệp mà không thực hiện upload.

        Raises:
            HTTPException: Khi xảy ra lỗi trong quá trình xác thực.
        """
        try:
            logger.info(f"[VALIDATE] Bắt đầu kiểm tra tệp: {file_name}")
 
            # Gọi service để thực hiện xác thực chi tiết
            result = self.upload_service.validate_file(
                file_content=file_content,
                file_name=file_name,
                mime_type=mime_type
            )
            
            # Ánh xạ kết quả validation sang schema phản hồi
            validation_result = ValidationResult(**result)
            
            message = "File hợp lệ" if result['is_valid'] else "File không hợp lệ"
            
            logger.info(f"[VALIDATE] Kết quả {file_name}: hợp lệ={result['is_valid']}")
            
            return SuccessResponse(
                message=message,
                data=validation_result
            )
            
        except Exception as e:
            logger.error(f"[VALIDATE] Lỗi không mong đợi: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Lỗi khi validate file"
            )