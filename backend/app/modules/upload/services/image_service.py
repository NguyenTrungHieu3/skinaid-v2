import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from sqlalchemy import text

from app.core.config import settings
from app.utils.constants.error_codes import *
from app.utils.exceptions.base_exceptions import AppBaseException
from app.modules.upload.models.wound_images import ImageInformation
from app.modules.upload.models.upload_validations import UploadValidation
from app.modules.upload.schemas.validation import (
    UploadValidationCreate,
    UploadValidationResponse
)

from app.modules.upload.services.file_service import FileService
from app.modules.upload.services.image_processing_service import ImageProcessingService
from app.modules.upload.services.image_validation_service import ImageValidationService
from app.modules.firstaid.services.first_aid_service import FirstAidService

logger = logging.getLogger(__name__)

class ImageService:
    """
    ImageService - UNIFIED IMAGE MANAGEMENT SERVICE

    Trách nhiệm DUY NHẤT: Quản lý toàn bộ vòng đời của hình ảnh
    - Upload và xử lý file
    - Quản lý database records (image information + validation)
    - Giao tiếp với AI service
    - Orchestration của toàn bộ workflow

    Pattern: Single Responsibility - một service duy nhất cho toàn bộ image management
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.file_service = FileService()
        self.image_processing_service = ImageProcessingService()
        self.first_aid_service = FirstAidService(db)
        self.validation_service = ImageValidationService()

    async def handle_image_upload_with_ai(
        self,
        user_id: str,
        file: UploadFile,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ORCHESTRATION METHOD - Điều phối toàn bộ workflow upload với AI
        """

        file_path = None
        wound_image_id = None

        try:
            logger.info(f"Validating file: {file.filename} for user: {user_id}")

            first_chunk = await file.read(1024)
            if not first_chunk:
                raise AppBaseException(
                    message="Cannot upload empty file",
                    error_code=FILE_EMPTY
                )
            validation_result = await self._validate_file_basic(file, first_chunk)
            if not validation_result["success"]:
                raise AppBaseException(
                    message=validation_result["error_message"],
                    error_code=validation_result["error_code"]
                )
            await file.seek(0)

            logger.info("Saving file to disk")

            file_path = self.file_service.generate_file_path(file.filename, user_id)
            save_result = await self.file_service.save_file(file, file_path)

            if not save_result["success"]:
                raise AppBaseException(
                    message=save_result["error_message"],
                    error_code=save_result["error_code"]
                )

            logger.info(f"File saved: {file_path}")

            logger.info("Creating database record")
            width, height = 512, 512  

            image_information = await self._create_image_information_record(
                woundhistory_id=user_id,
                filename=file.filename,
                file_path=file_path,
                file_size=save_result["file_size"],
                file_type=file.content_type,
                width=width,
                height=height
            )
            image_id = image_information.wound_images_id
            logger.info(f"Calling AI service for image: {image_id}")

            await self._update_image_status(image_id, "processing")
            full_image_path = os.path.join(settings.UPLOAD_DIR, file_path)
            ai_result = await self.image_processing_service.analyze_image(full_image_path)
            if not ai_result["success"] or ai_result["num_detections"] == 0:
                logger.warning("No wounds detected or AI service error")

                await self._update_image_status(
                    image_id,
                    "completed",
                    error_message="Không phát hiện vết thương hoặc AI service lỗi"
                )

                return {
                    "success": True,
                    "message": "Upload thành công nhưng không phát hiện vết thương",
                    "image_information": image_information,
                    "ai_result": None,
                    "first_aid": None
                }

            detection = ai_result["detections"][0]

            logger.info("Saving AI results to model_result table")

            model_result = await self._create_model_result(
                wound_images_id=image_id,
                wound_type=detection["class_name"],
                confidence_score=detection["confidence"],
                severity=detection["severity"],
                ai_model_version=ai_result.get("ai_model_version", "unknown"),
                processing_time_ms=int(ai_result.get("processing_time", 0) * 1000)
            )

            logger.info("Getting first aid guide")

            first_aid = await self.first_aid_service.get_first_aid_guide(
                wound_type=detection["class_name"],
                severity=detection["severity"]
            )

            logger.info("Upload workflow completed successfully")

            return {
                "success": True,
                "message": "Phân tích thành công",
                "image_information": image_information,
                "model_result": model_result.to_response_dict() if model_result else None,
                "ai_result": {
                    "wound_type": detection["class_name"],
                    "confidence": detection["confidence"],
                    "severity": detection["severity"],
                    "bbox": detection["bbox"],
                    "num_detections": ai_result["num_detections"]
                },
                "first_aid": first_aid
            }

        except AppBaseException:
            raise

        except Exception as e:
            logger.error(f"Unexpected error in upload workflow: {e}")

            if image_id:
                await self._update_image_status(
                    image_id,
                    "failed",
                    error_message=str(e)
                )

            if file_path:
                self.file_service.delete_file(file_path)

            raise AppBaseException(
                message="Upload failed due to an internal error.",
                error_code=FILE_UPLOAD_FAILED
            )

    async def handle_image_upload(
        self,
        user_id: str,
        file: UploadFile,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        SIMPLE UPLOAD - Upload không có AI processing
        """

        file_path = None

        try:
            logger.info(f"Basic validation for file: {file.filename}")

            first_chunk = await file.read(1024)
            if not first_chunk:
                raise AppBaseException(
                    message="Cannot upload empty file",
                    error_code=FILE_EMPTY
                )

            validation_result = await self._validate_file_basic(file, first_chunk)
            if not validation_result["success"]:
                raise AppBaseException(
                    message=validation_result["error_message"],
                    error_code=validation_result["error_code"]
                )

            await file.seek(0)

            logger.info("Saving file")

            file_path = self.file_service.generate_file_path(file.filename, user_id)
            save_result = await self.file_service.save_file(file, file_path)

            if not save_result["success"]:
                raise AppBaseException(
                    message=save_result["error_message"],
                    error_code=save_result["error_code"]
                )

            logger.info("Creating database record")

            width, height = 512, 512  

            image_information = await self._create_image_information_record(
                woundhistory_id=user_id,
                filename=file.filename,
                file_path=file_path,
                file_size=save_result["file_size"],
                file_type=file.content_type,
                width=width,
                height=height
            )

            await self._update_image_status(image_information.wound_images_id, "completed")

            logger.info(f"Simple upload completed: {image_information.wound_images_id}")

            return {"success": True, "data": image_information}

        except AppBaseException:
            raise

        except Exception as e:
            logger.error(f"Simple upload failed: {e}")

            if file_path:
                self.file_service.delete_file(file_path)

            raise AppBaseException(
                message="Upload failed due to an internal error.",
                error_code=FILE_UPLOAD_FAILED
            )

    async def get_image_by_id(self, wound_images_id: str, woundhistory_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin ảnh theo ID với kiểm tra quyền truy cập
        """
        try:
            sql = text("""
                SELECT * FROM image_information
                WHERE wound_images_id = :wound_images_id AND woundhistory_id = :woundhistory_id
            """)

            result = await self.db.execute(sql, {
                "wound_images_id": wound_images_id,
                "woundhistory_id": woundhistory_id
            })

            row = result.mappings().first()

            if not row:
                return {
                    "success": False,
                    "error_code": "IMAGE_NOT_FOUND",
                    "error_message": "Image not found or access denied"
                }

            image_information = ImageInformation.model_validate(dict(row))
            return {"success": True, "data": image_information}

        except Exception as e:
            logger.error(f"Failed to get image by ID: {e}")
            return {
                "success": False,
                "error_code": "IMAGE_RETRIEVAL_FAILED",
                "error_message": f"Failed to retrieve image: {str(e)}"
            }

    async def get_user_images(self, woundhistory_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        Lấy danh sách ảnh của user với pagination
        """
        try:
            count_sql = text("""
                SELECT COUNT(*) as total FROM image_information
                WHERE woundhistory_id = :woundhistory_id
            """)

            count_result = await self.db.execute(count_sql, {"woundhistory_id": woundhistory_id})
            count_row = count_result.mappings().first()
            total = count_row["total"] if count_row else 0

            sql = text("""
                SELECT * FROM image_information
                WHERE woundhistory_id = :woundhistory_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)

            result = await self.db.execute(sql, {
                "woundhistory_id": woundhistory_id,
                "limit": limit,
                "offset": offset
            })

            rows = result.mappings().all()
            images = [ImageInformation.model_validate(dict(row)) for row in rows]

            return {
                "success": True,
                "data": images,
                "total": total,
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            logger.error(f"Failed to get user images: {e}")
            return {
                "success": False,
                "error_code": "IMAGES_RETRIEVAL_FAILED",
                "error_message": f"Failed to retrieve user images: {str(e)}"
            }

    async def get_image_statistics(self, woundhistory_id: str) -> Dict[str, Any]:
        """
        Lấy thống kê ảnh của user
        """
        try:
            total_sql = text("""
                SELECT COUNT(*) as total FROM image_information
                WHERE woundhistory_id = :woundhistory_id
            """)

            total_result = await self.db.execute(total_sql, {"woundhistory_id": woundhistory_id})
            total_row = total_result.mappings().first()
            total_images = total_row["total"] if total_row else 0

            status_counts = {}
            for status in ["pending", "processing", "completed", "failed"]:
                status_sql = text("""
                    SELECT COUNT(*) as count FROM image_information
                    WHERE woundhistory_id = :woundhistory_id AND upload_status = :status
                """)

                status_result = await self.db.execute(status_sql, {
                    "woundhistory_id": woundhistory_id,
                    "status": status
                })
                status_row = status_result.mappings().first()
                status_counts[status] = status_row["count"] if status_row else 0

            return {
                "total_images": total_images,
                "status_breakdown": status_counts,
                "success_rate": (
                    status_counts.get("completed", 0) / total_images * 100
                    if total_images > 0 else 0
                )
            }

        except Exception as e:
            logger.error(f"Failed to get image statistics for {woundhistory_id}: {e}")
            return {
                "total_images": 0,
                "status_breakdown": {},
                "success_rate": 0
            }

    async def create_validation_record(
        self,
        validation_data: UploadValidationCreate,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UploadValidation:
        """
        Tạo bản ghi validation mới (đơn giản hóa - chỉ tạo record cơ bản)
        """
        try:
            sql = text("""
                INSERT INTO upload_validations (upload_validations_id, user_id, file_name, file_size, file_type, validation_passed, validation_errors, ip_address, user_agent, request_id, attempt_count, created_at, updated_at)
                VALUES (:upload_validations_id, :user_id, :file_name, :file_size, :file_type, :validation_passed, :validation_errors, :ip_address, :user_agent, :request_id, :attempt_count, :created_at, :updated_at)
                RETURNING *
            """)

            params = {
                "upload_validations_id": str(uuid.uuid4()),
                "user_id": validation_data.user_id,
                "file_name": validation_data.file_name,
                "file_size": validation_data.file_size,
                "file_type": validation_data.file_type,
                "validation_passed": validation_data.validation_passed,
                "validation_errors": validation_data.validation_errors,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_id": request_id or str(uuid.uuid4()),
                "attempt_count": 1,
                "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
            }

            result = await self.db.execute(sql, params)
            row = result.mappings().first()

            if not row:
                raise Exception("Failed to get returning row after insert.")

            return UploadValidation.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Failed to create validation record: {e}")
            await self.db.rollback()
            raise

    async def get_validation_by_id(self, validation_id: str) -> Optional[UploadValidation]:
        """
        Lấy validation record theo ID
        """
        try:
            sql = text("""
                SELECT * FROM upload_validations
                WHERE upload_validations_id = :validation_id
            """)

            result = await self.db.execute(sql, {"validation_id": validation_id})
            row = result.mappings().first()

            if not row:
                return None

            return UploadValidation.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Failed to get validation by ID {validation_id}: {e}")
            return None

    async def get_user_validations(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[UploadValidation]:
        """
        Lấy danh sách validation records của user
        """
        try:
            sql = text("""
                SELECT * FROM upload_validations
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)

            result = await self.db.execute(sql, {
                "user_id": user_id,
                "limit": limit,
                "offset": offset
            })

            rows = result.mappings().all()
            return [UploadValidation.model_validate(dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get user validations for {user_id}: {e}")
            return []

    async def _validate_file_basic(self, file: UploadFile, first_chunk: bytes) -> Dict[str, Any]:
        """
        Enhanced file validation sử dụng ImageValidationService
        """
        if not file.filename:
            return {
                "success": False,
                "error_code": VALIDATION_ERROR,
                "error_message": "Filename is missing"
            }

        validation_result = self.validation_service.validate_file(
            file_data=first_chunk,
            filename=file.filename,
            mime_type=file.content_type
        )

        if validation_result["success"]:
            validation_result["file_info"]["size"] = len(first_chunk)

        return validation_result

    async def _create_image_information_record(
        self,
        woundhistory_id: str,
        filename: str,
        file_path: str,
        file_size: int,
        file_type: str,
        width: int,
        height: int
    ) -> ImageInformation:
        """
        Tạo record trong bảng image_information
        """
        try:
            sql = text("""
                INSERT INTO image_information (wound_images_id, woundhistory_id, upload_status, file_name, file_path, file_size, file_type, width, height, created_at, updated_at)
                VALUES (:wound_images_id, :woundhistory_id, :upload_status, :file_name, :file_path, :file_size, :file_type, :width, :height, :created_at, :updated_at)
                RETURNING *
            """)

            params = {
                "wound_images_id": str(uuid.uuid4()),
                "woundhistory_id": woundhistory_id,
                "upload_status": "pending",
                "file_name": filename,
                "file_path": file_path,
                "file_size": file_size,
                "file_type": file_type,
                "width": width,
                "height": height,
                "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
            }

            result = await self.db.execute(sql, params)
            row = result.mappings().first()

            if not row:
                raise Exception("Failed to get returning row after insert.")

            return ImageInformation.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Failed to create wound image record: {e}")
            await self.db.rollback()
            raise AppBaseException(
                message="Could not save image record",
                error_code=FILE_UPLOAD_FAILED
            )

    async def _update_image_status(
        self,
        wound_images_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """
        Cập nhật trạng thái của image_information
        """
        try:
            sql = text("""
                UPDATE image_information
                SET upload_status = :status, error_message = :error_message, updated_at = :updated_at
                WHERE wound_images_id = :wound_images_id
            """)

            params = {
                "status": status,
                "error_message": error_message,
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "wound_images_id": wound_images_id
            }

            await self.db.execute(sql, params)
            await self.db.commit()

            logger.info(f"Updated image {wound_images_id} status to: {status}")

        except Exception as e:
            logger.error(f"Failed to update image status: {e}")
            await self.db.rollback()

    async def _create_model_result(
        self,
        wound_images_id: str,
        wound_type: str,
        confidence_score: float,
        severity: str,
        ai_model_version: str,
        processing_time_ms: int
    ):
        """Create model_result record with AI detection results"""
        try:
            from app.modules.ai.models.ai_analysis import ModelResult

            model_result = ModelResult(
                wound_images_id=wound_images_id,
                wound_type=wound_type,
                confidence_score=confidence_score,
                severity=severity,
                ai_model_version=ai_model_version,
                processing_time_ms=processing_time_ms
            )

            self.db.add(model_result)
            await self.db.commit()
            await self.db.refresh(model_result)

            return model_result

        except Exception as e:
            logger.error(f"Failed to create model result: {e}")
            raise