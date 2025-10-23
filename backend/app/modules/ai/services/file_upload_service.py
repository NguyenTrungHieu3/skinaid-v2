from fastapi import UploadFile
from typing import Tuple, Optional
import logging
import os
import aiofiles
import uuid
from datetime import datetime
from app.core.config import settings
from app.shared.schemas.response import ErrorResponse

logger = logging.getLogger(__name__)


class FileUploadService:
    UPLOAD_DIR = getattr(settings, 'UPLOAD_DIR', "./uploads")
    BASE_URL = getattr(settings, 'BASE_URL', "http://localhost:8000")
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_TYPES = ["image/jpeg", "image/png", "image/jpg"]

    @classmethod
    def generate_image_path(
        cls,
        user_id: uuid.UUID,
        original_filename: str
    ) -> Tuple[str, str, str]:
        """
        Generate unique file path.
        """
        now = datetime.now()
        date_path = now.strftime("%Y/%m/%d")
        timestamp = int(now.timestamp())
        unique_id = str(uuid.uuid4())[:8]

        file_ext = os.path.splitext(original_filename)[1].lower() or ".jpg"
        new_filename = f"{user_id}_{timestamp}_{unique_id}{file_ext}"
        
        relative_path = f"{date_path}/{new_filename}"
        full_path = os.path.join(cls.UPLOAD_DIR, date_path, new_filename)
        image_url = f"{cls.BASE_URL}/uploads/{relative_path}"

        return full_path, relative_path, image_url

    @classmethod
    async def save_file(cls, file: UploadFile, file_path: str) -> bytes:
        """
        Save uploaded file to disk.
        """
        try:
            content = await file.read()
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)

            logger.debug(f"[FILE] Saved: {file_path} ({len(content)} bytes)")
            return content

        except Exception as e:
            logger.error(f"[FILE] Save failed: {e}")
            raise

    @classmethod
    def validate_file(cls, file: UploadFile, content: bytes) -> Optional[ErrorResponse]:
        """
        Validate file type and size.
        """
        # Check empty
        if not file or not content:
            return ErrorResponse(
                message="File is empty or corrupted",
                error_code="INVALID_FILE",
                error_details={"file_size": len(content) if content else 0}
            )

        # Check type
        if file.content_type not in cls.ALLOWED_TYPES:
            logger.warning(f"[VALIDATE] Invalid type: {file.content_type}")
            return ErrorResponse(
                message=f"Invalid file type: {file.content_type}",
                error_code="INVALID_FILE_TYPE",
                error_details={
                    "content_type": file.content_type,
                    "allowed_types": cls.ALLOWED_TYPES
                }
            )

        # Check size
        if len(content) > cls.MAX_FILE_SIZE:
            logger.warning(
                f"[VALIDATE] File too large: {len(content)} bytes "
                f"({len(content) / 1024 / 1024:.2f} MB)"
            )
            return ErrorResponse(
                message="File too large. Max 5MB allowed.",
                error_code="FILE_TOO_LARGE",
                error_details={
                    "file_size": len(content),
                    "file_size_mb": round(len(content) / 1024 / 1024, 2),
                    "max_size": cls.MAX_FILE_SIZE,
                    "max_size_mb": 5
                }
            )

        logger.debug(f"[VALIDATE] File OK: {file.filename} ({len(content)} bytes)")
        return None

    @classmethod
    def cleanup_file(cls, file_path: str) -> None:
        """Remove uploaded file (used on error)."""
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"[CLEANUP] Removed: {file_path}")
            except Exception as e:
                logger.warning(f"[CLEANUP] Failed to remove {file_path}: {e}")