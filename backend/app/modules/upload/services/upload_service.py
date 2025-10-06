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
from app.modules.upload.models.wound_images import WoundImages

# Import các services chuyên biệt
from app.modules.upload.services.file_service import FileService
from app.modules.upload.services.image_processing_service import ImageProcessingService
from app.modules.firstaid.services.first_aid_service import FirstAidService

logger = logging.getLogger(__name__)

class UploadService:
    """
    🔄 UploadService - ORCHESTRATION LAYER

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
        🔄 ORCHESTRATION METHOD - Điều phối toàn bộ workflow upload

        Workflow:
        1. Validate file (giao cho validation service)
        2. Save file (giao cho file service)
        3. Create database record (giao cho database)
        4. Call AI service (giao cho image processing service)
        5. Update record with AI results
        6. Get first aid guide (giao cho first aid service)
        7. Return complete response

        ✅ Đơn giản: Chỉ orchestrate, không chứa business logic
        ✅ Dễ test: Có thể mock từng service
        ✅ Dễ maintain: Mỗi service thay đổi độc lập
        """

        file_path = None
        wound_image_id = None

        try:
            # ===== STEP 1: VALIDATE FILE =====
            logger.info(f"🔍 Validating file: {file.filename} for user: {user_id}")

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
            logger.info("💾 Saving file to disk")

            file_path = self.file_service.generate_file_path(file.filename, user_id)
            save_result = await self.file_service.save_file(file, file_path)

            if not save_result["success"]:
                raise AppBaseException(
                    message=save_result["error_message"],
                    error_code=save_result["error_code"]
                )

            logger.info(f"✅ File saved: {file_path}")

            # ===== STEP 3: CREATE DATABASE RECORD =====
            logger.info("🗄️ Creating database record")

            wound_image = await self._create_wound_image_record(
                user_id=user_id,
                filename=file.filename,
                file_path=file_path,
                file_size=save_result["file_size"],
                file_type=file.content_type
            )
            wound_image_id = wound_image.id

            # ===== STEP 4: CALL AI SERVICE =====
            logger.info(f"🤖 Calling AI service for image: {wound_image_id}")

            await self._update_image_status(wound_image_id, "processing")
            full_image_path = os.path.join(settings.UPLOAD_DIR, file_path)
            ai_result = await self.image_processing_service.analyze_image(full_image_path)

            # ===== STEP 5: PROCESS AI RESULTS =====
            if not ai_result["success"] or ai_result["num_detections"] == 0:
                logger.warning("⚠️ No wounds detected or AI service error")

                await self._update_image_status(
                    wound_image_id,
                    "completed",
                    error_message="Không phát hiện vết thương hoặc AI service lỗi"
                )

                return {
                    "success": True,
                    "message": "Upload thành công nhưng không phát hiện vết thương",
                    "wound_image": wound_image,
                    "ai_result": None,
                    "first_aid": None
                }

            # Lấy detection đầu tiên (highest confidence)
            detection = ai_result["detections"][0]

            # ===== STEP 6: UPDATE DATABASE WITH AI RESULTS =====
            logger.info("💾 Updating database with AI results")

            await self._update_wound_image_with_ai_result(
                image_id=wound_image_id,
                wound_type=detection["class_name"],
                confidence_score=detection["confidence"],
                severity=detection["severity"],
                ai_model_version=ai_result["ai_model_version"],
                processing_time_ms=int(ai_result["processing_time"] * 1000)
            )

            # ===== STEP 7: GET FIRST AID GUIDE =====
            logger.info("🩹 Getting first aid guide")

            first_aid = await self.first_aid_service.get_first_aid_guide(
                wound_type=detection["class_name"],
                severity=detection["severity"]
            )

            # ===== STEP 8: RETURN COMPLETE RESPONSE =====
            logger.info("✅ Upload workflow completed successfully")

            return {
                "success": True,
                "message": "Phân tích thành công",
                "wound_image": wound_image,
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
            logger.error(f"❌ Unexpected error in upload workflow: {e}")

            # Cleanup: update database status và delete file
            if wound_image_id:
                await self._update_image_status(
                    wound_image_id,
                    "failed",
                    error_message=str(e)
                )

            if file_path:
                self.file_service.delete_file(file_path)

            raise AppBaseException(
                message="Upload failed due to an internal error.",
                error_code=FILE_UPLOAD_FAILED
            )

    async def _update_wound_image_with_ai_result(
        self,
        image_id: str,
        wound_type: str,
        confidence_score: float,
        severity: str,
        ai_model_version: str,
        processing_time_ms: int
    ) -> None:
        """Update wound_images record with AI detection results"""
        try:
            sql = text("""
                UPDATE wound_images
                SET wound_type = :wound_type,
                    confidence_score = :confidence_score,
                    severity = :severity,
                    ai_model_version = :ai_model_version,
                    processing_time_ms = :processing_time_ms,
                    upload_status = 'completed',
                    processed_at = :processed_at,
                    updated_at = :updated_at
                WHERE id = :image_id
            """)
            
            await self.db.execute(sql, {
                "wound_type": wound_type,
                "confidence_score": confidence_score,
                "severity": severity,
                "ai_model_version": ai_model_version,
                "processing_time_ms": processing_time_ms,
                "processed_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "image_id": image_id
            })
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update wound image with AI result: {e}")
            raise

    async def _get_first_aid_guide(
        self,
        wound_type: str,
        severity: str
    ) -> Optional[Dict[str, Any]]:
        """Query first aid guide from database"""
        try:
            sql = text("""
                SELECT *
                FROM firstaidguides
                WHERE wound_type = :wound_type AND severity = :severity
                LIMIT 1
            """)
            
            result = await self.db.execute(sql, {
                "wound_type": wound_type,
                "severity": severity
            })
            
            row = result.mappings().first()
            
            if not row:
                logger.warning(f"No first aid guide found for {wound_type}/{severity}")
                return None
            
            return dict(row)
            
        except Exception as e:
            logger.error(f"Failed to get first aid guide: {e}")
            return None

    async def handle_image_upload(
        self,
        user_id: str,
        file: UploadFile,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        📤 SIMPLE UPLOAD - Upload không có AI processing

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
            logger.info(f"🔍 Basic validation for file: {file.filename}")

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
            logger.info("💾 Saving file")

            file_path = self.file_service.generate_file_path(file.filename, user_id)
            save_result = await self.file_service.save_file(file, file_path)

            if not save_result["success"]:
                raise AppBaseException(
                    message=save_result["error_message"],
                    error_code=save_result["error_code"]
                )

            # ===== STEP 3: CREATE DATABASE RECORD =====
            logger.info("🗄️ Creating database record")

            wound_image = await self._create_wound_image_record(
                user_id=user_id,
                filename=file.filename,
                file_path=file_path,
                file_size=save_result["file_size"],
                file_type=file.content_type
            )

            # Set status to completed (no AI processing)
            await self._update_image_status(wound_image.id, "completed")

            logger.info(f"✅ Simple upload completed: {wound_image.id}")

            return {"success": True, "data": wound_image}

        except AppBaseException:
            raise

        except Exception as e:
            logger.error(f"❌ Simple upload failed: {e}")

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

    async def _create_wound_image_record(
        self,
        user_id: str,
        filename: str,
        file_path: str,
        file_size: int,
        file_type: str
    ) -> WoundImages:
        """
        Tạo record trong bảng wound_images

        Args:
            user_id: ID của user upload
            filename: Tên file gốc
            file_path: Đường dẫn file đã lưu
            file_size: Kích thước file (bytes)
            file_type: MIME type

        Returns:
            WoundImages object
        """
        try:
            sql = text("""
                INSERT INTO wound_images (id, user_id, file_name, file_path, file_size, file_type, upload_status, created_at, updated_at)
                VALUES (:id, :user_id, :file_name, :file_path, :file_size, :file_type, :upload_status, :created_at, :updated_at)
                RETURNING *
            """)

            params = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "file_name": filename,
                "file_path": file_path,
                "file_size": file_size,
                "file_type": file_type,
                "upload_status": "pending",
                "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
            }

            result = await self.db.execute(sql, params)
            row = result.mappings().first()

            if not row:
                raise Exception("Failed to get returning row after insert.")

            return WoundImages.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Failed to create wound image record: {e}")
            raise AppBaseException(
                message="Could not save image record",
                error_code=FILE_UPLOAD_FAILED
            )

    async def _update_image_status(
        self,
        image_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """
        Cập nhật trạng thái của wound_image

        Args:
            image_id: ID của record cần update
            status: Trạng thái mới (pending, processing, completed, failed)
            error_message: Thông báo lỗi (optional)
        """
        try:
            sql = text("""
                UPDATE wound_images
                SET upload_status = :status, error_message = :error_message, updated_at = :updated_at
                WHERE id = :image_id
            """)

            params = {
                "status": status,
                "error_message": error_message,
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "image_id": image_id
            }

            await self.db.execute(sql, params)
            await self.db.commit()

            logger.info(f"Updated image {image_id} status to: {status}")

        except Exception as e:
            logger.error(f"Failed to update image status: {e}")
            # Không raise exception vì đây là operation phụ

    async def _update_wound_image_with_ai_result(
        self,
        image_id: str,
        wound_type: str,
        confidence_score: float,
        severity: str,
        ai_model_version: str,
        processing_time_ms: int
    ) -> None:
        """
        Cập nhật kết quả AI vào wound_images record

        Args:
            image_id: ID của record cần update
            wound_type: Loại vết thương từ AI
            confidence_score: Độ tin cậy từ AI (0-1)
            severity: Mức độ nghiêm trọng (mild, moderate, severe)
            ai_model_version: Version của AI model
            processing_time_ms: Thời gian xử lý (milliseconds)
        """
        try:
            sql = text("""
                UPDATE wound_images
                SET wound_type = :wound_type,
                    confidence_score = :confidence_score,
                    severity = :severity,
                    ai_model_version = :ai_model_version,
                    processing_time_ms = :processing_time_ms,
                    upload_status = 'completed',
                    processed_at = :processed_at,
                    updated_at = :updated_at
                WHERE id = :image_id
            """)

            await self.db.execute(sql, {
                "wound_type": wound_type,
                "confidence_score": confidence_score,
                "severity": severity,
                "ai_model_version": ai_model_version,
                "processing_time_ms": processing_time_ms,
                "processed_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "image_id": image_id
            })

            await self.db.commit()

            logger.info(
                f"Updated AI results for image {image_id}",
                extra={
                    "wound_type": wound_type,
                    "confidence": confidence_score,
                    "severity": severity,
                    "processing_time_ms": processing_time_ms
                }
            )

        except Exception as e:
            logger.error(f"Failed to update wound image with AI result: {e}")
            raise AppBaseException(
                message="Failed to save AI results",
                error_code="AI_RESULT_SAVE_FAILED"
            )
    
    async def get_image_by_id(self, image_id: str, user_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin ảnh theo ID (cho user đó)

        Args:
            image_id: ID của ảnh
            user_id: ID của user (để kiểm tra quyền truy cập)

        Returns:
            Dict chứa kết quả hoặc error
        """
        try:
            sql = text("""
                SELECT * FROM wound_images
                WHERE id = :image_id AND user_id = :user_id
            """)

            result = await self.db.execute(sql, {
                "image_id": image_id,
                "user_id": user_id
            })

            row = result.mappings().first()

            if not row:
                return {
                    "success": False,
                    "error_code": "IMAGE_NOT_FOUND",
                    "error_message": "Image not found or access denied"
                }

            wound_image = WoundImages.model_validate(dict(row))
            return {"success": True, "data": wound_image}

        except Exception as e:
            logger.error(f"Failed to get image by ID: {e}")
            return {
                "success": False,
                "error_code": "IMAGE_RETRIEVAL_FAILED",
                "error_message": f"Failed to retrieve image: {str(e)}"
            }

    async def get_user_images(self, user_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        Lấy danh sách ảnh của user với pagination

        Args:
            user_id: ID của user
            limit: Số lượng ảnh tối đa (default: 20)
            offset: Số ảnh bỏ qua (default: 0)

        Returns:
            Dict chứa danh sách ảnh và tổng số
        """
        try:
            # Đếm tổng số ảnh
            count_sql = text("""
                SELECT COUNT(*) as total FROM wound_images
                WHERE user_id = :user_id
            """)

            count_result = await self.db.execute(count_sql, {"user_id": user_id})
            count_row = count_result.mappings().first()
            total = count_row["total"] if count_row else 0

            # Lấy danh sách ảnh (có pagination)
            sql = text("""
                SELECT * FROM wound_images
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
            images = [WoundImages.model_validate(dict(row)) for row in rows]

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