import os
import uuid
import aiofiles
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from fastapi import UploadFile
import logging

from app.core.config import settings
from app.utils.constants.error_codes import *

logger = logging.getLogger(__name__)

class FileService:
    """
    FileService - FILE OPERATIONS SPECIALIST

    Trách nhiệm DUY NHẤT: Xử lý tất cả thao tác liên quan đến file
    - File validation (size, format, dimensions)
    - File saving và cleanup
    - File path generation
    - Directory management
    """

    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.chunk_size = 1024 * 1024  # 1MB chunks
        self._ensure_upload_directory()

    def _ensure_upload_directory(self) -> None:
        """Đảm bảo thư mục upload tồn tại"""
        os.makedirs(self.upload_dir, exist_ok=True)
        logger.info(f"Thư mục tải lên đã sẵn sàng: {self.upload_dir}")

    def generate_file_path(self, original_filename: str, user_id: str) -> str:
        """
        Tạo đường dẫn file unique với format: YYYY/MM/DD/user_id_timestamp_uuid.ext

        Args:
            original_filename: Tên file gốc từ user
            user_id: ID của user upload

        Returns:
            str: Đường dẫn relative từ upload_dir
        """
        _, ext = os.path.splitext(original_filename)
        now = datetime.now(timezone.utc)
        date_path = now.strftime("%Y/%m/%d")
        timestamp = int(now.timestamp())
        unique_id = uuid.uuid4().hex[:8]
        new_filename = f"{user_id}_{timestamp}_{unique_id}{ext}"

        file_path = os.path.join(date_path, new_filename).replace("\\", "/")
        logger.info(f"Đã tạo đường dẫn file: {file_path}")

        return file_path

    async def save_file(self, file: UploadFile, file_path: str) -> Dict[str, Any]:
        """
        Lưu file vào disk với error handling tốt

        Args:
            file: UploadFile từ FastAPI
            file_path: Đường dẫn relative để lưu

        Returns:
            Dict chứa kết quả save hoặc error

        Raises:
            Không raise exception - trả về error dict để caller handle
        """
        full_path = os.path.join(self.upload_dir, file_path)

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            file_size = 0
            await file.seek(0)
            async with aiofiles.open(full_path, 'wb') as f:
                while chunk := await file.read(self.chunk_size):
                    await f.write(chunk)
                    file_size += len(chunk)

            logger.info(f"Lưu file thành công: {file_path} ({file_size} bytes)")
            return {
                "success": True,
                "file_path": file_path,
                "full_path": full_path,
                "file_size": file_size
            }

        except Exception as e:
            logger.error(f"Không thể lưu file {file_path}: {e}")
            return {
                "success": False,
                "error_code": FILE_SAVE_FAILED,
                "error_message": f"Không thể lưu file: {str(e)}"
            }

    def delete_file(self, file_path: str) -> bool:
        """
        Xóa file khỏi disk

        Args:
            file_path: Đường dẫn relative từ upload_dir

        Returns:
            bool: True nếu xóa thành công
        """
        full_path = os.path.join(self.upload_dir, file_path)

        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"Đã xóa file: {file_path}")
                return True
            else:
                logger.warning(f"Không tìm thấy file để xóa: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Không thể xóa file {file_path}: {e}")
            return False

    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        Lấy kích thước file

        Args:
            file_path: Đường dẫn relative từ upload_dir

        Returns:
            int: Kích thước file (bytes) hoặc None nếu lỗi
        """
        full_path = os.path.join(self.upload_dir, file_path)

        try:
            return os.path.getsize(full_path)
        except Exception as e:
            logger.error(f"Không thể lấy kích thước file {file_path}: {e}")
            return None

    def file_exists(self, file_path: str) -> bool:
        """
        Kiểm tra file có tồn tại không

        Args:
            file_path: Đường dẫn relative từ upload_dir

        Returns:
            bool: True nếu file tồn tại
        """
        full_path = os.path.join(self.upload_dir, file_path)
        return os.path.exists(full_path)