from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
import uuid
from datetime import datetime, timezone

from app.modules.upload.models.wound_images import ImageInformation
from app.modules.upload.schemas.upload import WoundImageDetail

logger = logging.getLogger(__name__)


class ImageInformationService:
    """Service chuyên biệt để quản lý ImageInformation model"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_image_record(
        self,
        woundhistory_id: str,
        file_name: str,
        file_path: str,
        file_size: int,
        file_type: str,
        width: int,
        height: int,
        upload_status: str = "pending"
    ) -> ImageInformation:
        """
        Tạo mới một image information record

        Args:
            woundhistory_id: ID của wound history
            file_name: Tên file gốc
            file_path: Đường dẫn file đã lưu
            file_size: Kích thước file (bytes)
            file_type: MIME type
            width: Chiều rộng ảnh
            height: Chiều cao ảnh
            upload_status: Trạng thái upload (default: "pending")

        Returns:
            ImageInformation object đã được tạo
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
                "upload_status": upload_status,
                "file_name": file_name,
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
            logger.error(f"Failed to create image information record: {e}")
            await self.db.rollback()
            raise

    async def get_image_by_id(self, image_id: str) -> Optional[ImageInformation]:
        """
        Lấy thông tin ảnh theo ID

        Args:
            image_id: ID của ảnh

        Returns:
            ImageInformation object hoặc None nếu không tìm thấy
        """
        try:
            sql = text("""
                SELECT * FROM image_information
                WHERE wound_images_id = :image_id
            """)

            result = await self.db.execute(sql, {"image_id": image_id})
            row = result.mappings().first()

            if not row:
                return None

            return ImageInformation.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Failed to get image by ID {image_id}: {e}")
            return None

    async def get_image_by_wound_history(
        self,
        woundhistory_id: str,
        image_id: str
    ) -> Optional[ImageInformation]:
        """
        Lấy thông tin ảnh theo wound history ID và image ID (kiểm tra quyền truy cập)

        Args:
            woundhistory_id: ID của wound history
            image_id: ID của ảnh

        Returns:
            ImageInformation object hoặc None nếu không tìm thấy hoặc không có quyền
        """
        try:
            sql = text("""
                SELECT * FROM image_information
                WHERE wound_images_id = :image_id AND woundhistory_id = :woundhistory_id
            """)

            result = await self.db.execute(sql, {
                "image_id": image_id,
                "woundhistory_id": woundhistory_id
            })
            row = result.mappings().first()

            if not row:
                return None

            return ImageInformation.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Failed to get image by wound history {woundhistory_id} and image {image_id}: {e}")
            return None

    async def update_image_status(
        self,
        image_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[ImageInformation]:
        """
        Cập nhật trạng thái của image

        Args:
            image_id: ID của ảnh
            status: Trạng thái mới
            error_message: Thông báo lỗi (optional)

        Returns:
            ImageInformation object đã được cập nhật hoặc None nếu không tìm thấy
        """
        try:
            sql = text("""
                UPDATE image_information
                SET upload_status = :status, error_message = :error_message, updated_at = :updated_at
                WHERE wound_images_id = :image_id
                RETURNING *
            """)

            params = {
                "status": status,
                "error_message": error_message,
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "image_id": image_id
            }

            result = await self.db.execute(sql, params)
            await self.db.commit()
            row = result.mappings().first()

            if not row:
                return None

            return ImageInformation.model_validate(dict(row))

        except Exception as e:
            logger.error(f"Failed to update image status for {image_id}: {e}")
            await self.db.rollback()
            return None

    async def get_user_images(
        self,
        woundhistory_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[ImageInformation]:
        """
        Lấy danh sách ảnh của user với pagination

        Args:
            woundhistory_id: ID của wound history
            limit: Số lượng ảnh tối đa
            offset: Số ảnh bỏ qua

        Returns:
            List các ImageInformation objects
        """
        try:
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
            return [ImageInformation.model_validate(dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get user images for {woundhistory_id}: {e}")
            return []

    async def get_images_by_status(
        self,
        status: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[ImageInformation]:
        """
        Lấy danh sách ảnh theo trạng thái

        Args:
            status: Trạng thái cần lọc
            limit: Số lượng ảnh tối đa
            offset: Số ảnh bỏ qua

        Returns:
            List các ImageInformation objects
        """
        try:
            sql = text("""
                SELECT * FROM image_information
                WHERE upload_status = :status
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)

            result = await self.db.execute(sql, {
                "status": status,
                "limit": limit,
                "offset": offset
            })

            rows = result.mappings().all()
            return [ImageInformation.model_validate(dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get images by status {status}: {e}")
            return []

    async def delete_image_record(self, image_id: str) -> bool:
        """
        Xóa image record

        Args:
            image_id: ID của ảnh cần xóa

        Returns:
            True nếu xóa thành công, False nếu không tìm thấy
        """
        try:
            sql = text("""
                DELETE FROM image_information
                WHERE wound_images_id = :image_id
            """)

            result = await self.db.execute(sql, {"image_id": image_id})
            await self.db.commit()

            # Kiểm tra xem có row nào bị ảnh hưởng không
            if result.rowcount > 0:
                logger.info(f"Deleted image record: {image_id}")
                return True
            else:
                logger.warning(f"Image record not found: {image_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete image record {image_id}: {e}")
            await self.db.rollback()
            return False

    async def create_image_detail_response(self, image: ImageInformation) -> WoundImageDetail:
        """
        Tạo WoundImageDetail response từ ImageInformation model

        Args:
            image: ImageInformation object

        Returns:
            WoundImageDetail object
        """
        # Use the new to_detail_dict method if available
        if hasattr(image, 'to_detail_dict'):
            return WoundImageDetail(**image.to_detail_dict())
        else:
            # Fallback for backward compatibility
            return WoundImageDetail(
                id=image.wound_images_id,
                user_id=image.woundhistory_id,
                file_name=image.file_name,
                file_path=image.file_path,
                file_size=image.file_size,
                file_type=image.file_type,
                width=image.width,
                height=image.height,
                upload_status=image.upload_status,
                error_message=image.error_message,
                created_at=image.created_at,
                updated_at=image.updated_at
            )

    async def get_image_statistics(self, woundhistory_id: str) -> Dict[str, Any]:
        """
        Lấy thống kê ảnh của user

        Args:
            woundhistory_id: ID của wound history

        Returns:
            Dict chứa các thống kê
        """
        try:
            # Tổng số ảnh
            total_sql = text("""
                SELECT COUNT(*) as total FROM image_information
                WHERE woundhistory_id = :woundhistory_id
            """)

            total_result = await self.db.execute(total_sql, {"woundhistory_id": woundhistory_id})
            total_row = total_result.mappings().first()
            total_images = total_row["total"] if total_row else 0

            # Số ảnh theo trạng thái
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