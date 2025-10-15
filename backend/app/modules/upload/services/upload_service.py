import os
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from sqlalchemy import text

from app.core.config import settings
from app.utils.constants.error_codes import *
from app.utils.exceptions.base_exceptions import AppBaseException
from app.modules.upload.models.wound_images import ImageInformation

from app.modules.upload.services.file_service import FileService
from app.modules.upload.services.image_processing_service import ImageProcessingService
from app.modules.firstaid.services.first_aid_service import FirstAidService

logger = logging.getLogger(__name__)

class UploadService:
    """
    UploadService - ORCHESTRATION LAYER

    Trách nhiệm DUY NHẤT: Điều phối workflow upload
    - Không chứa business logic phức tạp
    - Không thao tác trực tiếp với file system
    - Không gọi AI service trực tiếp
    - Không query database trực tiếp

    Pattern: Route → Controller → Service → Specialized Services
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        # Inject các specialized services
        self.file_service = FileService()
        self.image_processing_service = ImageProcessingService()
        self.first_aid_service = FirstAidService(db)
    
    async def handle_image_upload_with_ai(
        self,
        user_id: str,
        file: UploadFile,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ORCHESTRATION METHOD - Điều phối toàn bộ workflow upload

        Workflow:
        1. Validate file (giao cho validation service)
        2. Save file (giao cho file service)
        3. Create database record (giao cho database)
        4. Call AI service (giao cho image processing service)
        5. Update record with AI results
        6. Get first aid guide (giao cho first aid service)
        7. Return complete response

        Đơn giản: Chỉ orchestrate, không chứa business logic
        De test: Có thể mock từng service
        De maintain: Mỗi service thay đổi độc lập
        """

        file_path = None
        wound_image_id = None

        try:
            # ===== STEP 1: VALIDATE FILE =====
            logger.info(f"Validating file: {file.filename} for user: {user_id}")

            # Đọc chunk đầu tiên để validate (không cần đọc toàn bộ file)
            first_chunk = await file.read(1024)
            if not first_chunk:
                raise AppBaseException(
                    message="Cannot upload empty file",
                    error_code=FILE_EMPTY
                )

            # Validate file (sẽ implement validation service sau)
            validation_result = await self._validate_file_basic(file, first_chunk)
            if not validation_result["success"]:
                raise AppBaseException(
                    message=validation_result["error_message"],
                    error_code=validation_result["error_code"]
                )

            # Reset file pointer về đầu để đọc lại
            await file.seek(0)

            # ===== STEP 2: SAVE FILE =====
            logger.info("Saving file to disk")

            file_path = self.file_service.generate_file_path(file.filename, user_id)
            save_result = await self.file_service.save_file(file, file_path)

            if not save_result["success"]:
                raise AppBaseException(
                    message=save_result["error_message"],
                    error_code=save_result["error_code"]
                )

            logger.info(f"File saved: {file_path}")

            # ===== STEP 3: CREATE DATABASE RECORD =====
            logger.info("Creating database record")

            # Get image dimensions (simplified - in real implementation, you'd analyze the image)
            width, height = 512, 512  # Default values for now

            image_information = await self._create_image_information_record(
                woundhistory_id=user_id,  # Using user_id as woundhistory_id for now
                filename=file.filename,
                file_path=file_path,
                file_size=save_result["file_size"],
                file_type=file.content_type,
                width=width,
                height=height
            )
            image_id = image_information.wound_images_id

            # ===== STEP 4: CALL AI SERVICE =====
            logger.info(f"Calling AI service for image: {image_id}")

            await self._update_image_status(image_id, "processing")
            full_image_path = os.path.join(settings.UPLOAD_DIR, file_path)
            ai_result = await self.image_processing_service.analyze_image(full_image_path)

            # ===== STEP 5: PROCESS AI RESULTS =====
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

            # Lấy detection đầu tiên (highest confidence)
            detection = ai_result["detections"][0]

            # ===== STEP 6: SAVE AI RESULTS TO MODEL_RESULT TABLE =====
            logger.info("Saving AI results to model_result table")

            # Create ModelResult record
            model_result = await self._create_model_result(
                wound_images_id=image_id,
                wound_type=detection["class_name"],
                confidence_score=detection["confidence"],
                severity=detection["severity"],
                ai_model_version=ai_result.get("ai_model_version", "unknown"),
                processing_time_ms=int(ai_result.get("processing_time", 0) * 1000)
            )

            # ===== STEP 7: GET FIRST AID GUIDE =====
            logger.info("Getting first aid guide")

            first_aid = await self.first_aid_service.get_first_aid_guide(
                wound_type=detection["class_name"],
                severity=detection["severity"]
            )

            # ===== STEP 8: RETURN COMPLETE RESPONSE =====
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
            # Re-raise business exceptions
            raise

        except Exception as e:
            # Handle unexpected errors
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

    async def handle_image_upload(
        self,
        user_id: str,
        file: UploadFile,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        SIMPLE UPLOAD - Upload không có AI processing

        Workflow đơn giản:
        1. Validate file cơ bản
        2. Save file
        3. Create database record
        4. Return success response

        Dùng cho trường hợp chỉ cần upload mà không cần AI analysis
        """

        file_path = None

        try:
            # ===== STEP 1: BASIC VALIDATION =====
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

            # ===== STEP 2: SAVE FILE =====
            logger.info("Saving file")

            file_path = self.file_service.generate_file_path(file.filename, user_id)
            save_result = await self.file_service.save_file(file, file_path)

            if not save_result["success"]:
                raise AppBaseException(
                    message=save_result["error_message"],
                    error_code=save_result["error_code"]
                )

            # ===== STEP 3: CREATE DATABASE RECORD =====
            logger.info("Creating database record")

            # Get image dimensions (simplified - in real implementation, you'd analyze the image)
            width, height = 512, 512  # Default values for now

            image_information = await self._create_image_information_record(
                woundhistory_id=user_id,  # Using user_id as woundhistory_id for now
                filename=file.filename,
                file_path=file_path,
                file_size=save_result["file_size"],
                file_type=file.content_type,
                width=width,
                height=height
            )

            # Set status to completed (no AI processing)
            await self._update_image_status(image_information.wound_images_id, "completed")

            logger.info(f"Simple upload completed: {image_information.wound_images_id}")

            return {"success": True, "data": image_information}

        except AppBaseException:
            raise

        except Exception as e:
            logger.error(f"Simple upload failed: {e}")

            # Cleanup
            if file_path:
                self.file_service.delete_file(file_path)

            raise AppBaseException(
                message="Upload failed due to an internal error.",
                error_code=FILE_UPLOAD_FAILED
            )

    async def _validate_file_basic(self, file: UploadFile, first_chunk: bytes) -> Dict[str, Any]:
        """
        Basic file validation (đơn giản hơn validation service đầy đủ)

        Args:
            file: UploadFile từ FastAPI
            first_chunk: 1024 bytes đầu tiên của file

        Returns:
            Dict chứa kết quả validation
        """
        # Check filename
        if not file.filename:
            return {
                "success": False,
                "error_code": VALIDATION_ERROR,
                "error_message": "Filename is missing"
            }

        # Check MIME type cơ bản
        allowed_types = ["image/jpeg", "image/png", "image/jpg"]
        if file.content_type not in allowed_types:
            return {
                "success": False,
                "error_code": "INVALID_FILE_TYPE",
                "error_message": f"Invalid file type: {file.content_type}"
            }

        # Check file size cơ bản (dưới 5MB)
        file_size = len(first_chunk)
        max_size = 5 * 1024 * 1024  # 5MB

        if file_size > max_size:
            return {
                "success": False,
                "error_code": "FILE_TOO_LARGE",
                "error_message": f"File too large: {file_size / 1024 / 1024:.2f}MB (max: 5MB)"
            }

        return {
            "success": True,
            "file_info": {
                "filename": file.filename,
                "size": file_size,
                "mime_type": file.content_type
            }
        }

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

        Args:
            woundhistory_id: ID của wound history
            filename: Tên file gốc
            file_path: Đường dẫn file đã lưu
            file_size: Kích thước file (bytes)
            file_type: MIME type
            width: Chiều rộng ảnh
            height: Chiều cao ảnh

        Returns:
            ImageInformation object
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

        Args:
            wound_images_id: ID của record cần update
            status: Trạng thái mới (pending, processing, completed, failed)
            error_message: Thông báo lỗi (optional)
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
    
    async def get_image_by_id(self, wound_images_id: str, woundhistory_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin ảnh theo ID

        Args:
            wound_images_id: ID của ảnh
            woundhistory_id: ID của wound history (để kiểm tra quyền truy cập)

        Returns:
            Dict chứa kết quả hoặc error
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

        Args:
            woundhistory_id: ID của wound history
            limit: Số lượng ảnh tối đa (default: 20)
            offset: Số ảnh bỏ qua (default: 0)

        Returns:
            Dict chứa danh sách ảnh và tổng số
        """
        try:
            # Đếm tổng số ảnh
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