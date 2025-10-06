import os
import re
import io
import logging
from typing import Dict, Any, Optional

try:
    import magic
    LIBMAGIC_AVAILABLE = True
except ImportError:
    LIBMAGIC_AVAILABLE = False
    magic = None

from PIL import Image
from fastapi import UploadFile

from app.core.config import settings
from app.utils.constants.error_codes import (
    FILE_CORRUPT,
    FILE_INVALID_TYPE,
    FILE_TOO_LARGE,
    FILE_UPLOAD_FAILED,
    FILE_EMPTY,
    FILE_INVALID_RESOLUTION,
    FILE_SAVE_FAILED,
    FILE_UNSAFE_FILENAME,
    VALIDATION_ERROR,
)

logger = logging.getLogger(__name__)


class ValidationService:
    def __init__(self):
        self.max_file_size = settings.UPLOAD_MAX_FILE_SIZE
        self.allowed_extensions = set(
            fmt.strip().lower() for fmt in settings.UPLOAD_ALLOWED_FORMATS.split(",")
        )
        self.min_width = settings.UPLOAD_MIN_WIDTH
        self.min_height = settings.UPLOAD_MIN_HEIGHT

        self.ext_mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }

        self.allowed_mime_types = {
            self.ext_mime_map[ext]
            for ext in self.allowed_extensions
            if ext in self.ext_mime_map
        }

        if LIBMAGIC_AVAILABLE and magic is not None:
            try:
                self.mime_validator = magic.Magic(mime=True)
            except Exception as e:
                logger.warning(f"Failed to initialize magic library: {e}")
                self.mime_validator = None
        else:
            self.mime_validator = None

    def _is_safe_filename(self, filename: str) -> bool:
        if "..." in filename or "/" in filename or "\\" in filename:
            return False
        if "\x00" in filename: 
            return False
        return True

    def _sanitize_filename(self, filename: str) -> str:
        filename = os.path.basename(filename)
        filename = re.sub(r"[^\w\s.-]", "", filename)
        filename = filename.replace(" ", "_")

        name, ext = os.path.splitext(filename)
        if len(name) > 100:
            name = name[:100]

        return f"{name}{ext}"

    def _get_file_extension(self, filename: str) -> str:
        if not filename:
            return ""
        _, ext = os.path.splitext(filename)
        return ext.lower()

    def _detect_mime(self, file_data: bytes, client_mime: Optional[str]) -> str:
        if self.mime_validator:
            try:
                return self.mime_validator.from_buffer(file_data)
            except Exception as e:
                logger.warning(f"[Validation] libmagic failed: {e}")
        return client_mime or "unknown"

    def _check_extension_mime_consistency(
        self, ext: str, detected_mime: str
    ) -> Optional[Dict[str, Any]]:
        expected_mime = self.ext_mime_map.get(ext)
        if expected_mime and detected_mime != "unknown":
            if detected_mime != expected_mime:
                return {
                    "success": False,
                    "error_code": FILE_INVALID_TYPE,
                    "error_message": (
                        f"Extension '{ext}' expects MIME '{expected_mime}', "
                        f"but detected '{detected_mime}'"
                    ),
                }
        return None

    def validate_image_file(
        self, file_data: bytes, filename: str, mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            # 1. Validate filename
            if not self._is_safe_filename(filename):
                return {
                    "success": False,
                    "error_code": FILE_UNSAFE_FILENAME,
                    "error_message": "Filename contains unsafe characters",
                }

            # 2. Validate file extension
            file_ext = self._get_file_extension(filename)
            if file_ext not in self.allowed_extensions:
                return {
                    "success": False,
                    "error_code": FILE_INVALID_TYPE,
                    "error_message": f"File extension '{file_ext}' not allowed. "
                    f"Allowed: {', '.join(sorted(self.allowed_extensions))}",
                }

            # 3. Detect MIME type
            actual_mime_type = self._detect_mime(file_data, mime_type)

            # 4. MIME whitelist check
            if (
                actual_mime_type != "unknown"
                and actual_mime_type not in self.allowed_mime_types
            ):
                logger.warning(
                    f"[Validation] MIME not allowed: {actual_mime_type} | "
                    f"filename={filename}, ext={file_ext}, client={mime_type}"
                )
                return {
                    "success": False,
                    "error_code": FILE_INVALID_TYPE,
                    "error_message": f"MIME type '{actual_mime_type}' not allowed",
                }

            # 5. Extension ↔ MIME consistency
            mismatch = self._check_extension_mime_consistency(
                file_ext, actual_mime_type
            )
            if mismatch:
                return mismatch

            # 6. Validate image properties
            try:
                image = Image.open(io.BytesIO(file_data))
                image.verify()

                image = Image.open(io.BytesIO(file_data))
                width, height = image.size
                image_format = image.format

                if width < self.min_width or height < self.min_height:
                    return {
                        "success": False,
                        "error_code": FILE_INVALID_RESOLUTION,
                        "error_message": f"Image resolution ({width}x{height}) "
                        f"is below minimum ({self.min_width}x{self.min_height})",
                    }

                return {
                    "success": True,
                    "file_info": {
                        "filename": self._sanitize_filename(filename),
                        "original_filename": filename,
                        "mime_type": actual_mime_type,
                        "width": width,
                        "height": height,
                        "format": image_format,
                    },
                }
            except (IOError, SyntaxError) as e:
                return {
                    "success": False,
                    "error_code": FILE_CORRUPT,
                    "error_message": f"Image file is corrupted or invalid: {str(e)}",
                }

        except Exception as e:
            logger.error(f"[Validation] Unexpected error: {str(e)} | filename={filename}")
            return {
                "success": False,
                "error_code": VALIDATION_ERROR,
                "error_message": f"Unexpected validation error: {str(e)}",
            }

    def validate_file_size(self, file_size: int) -> Dict[str, Any]:
        if file_size > self.max_file_size:
            size_mb = self.max_file_size / (1024 * 1024)
            return {
                "success": False,
                "error_code": FILE_TOO_LARGE,
                "error_message": f"File size exceeds maximum allowed size ({size_mb:.2f} MB)",
            }
        return {"success": True}
