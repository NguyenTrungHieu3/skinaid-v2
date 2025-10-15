import os
import re
import io
import logging
from typing import Optional, Dict, Any

try:
    import magic
    LIBMAGIC_AVAILABLE = True
except ImportError:
    LIBMAGIC_AVAILABLE = False
    magic = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

from app.core.config import settings
from app.utils.constants.error_codes import *

logger = logging.getLogger(__name__)


class ImageValidationService:
    """
    ImageValidationService - SPECIALIZED IMAGE VALIDATION SERVICE

    Trách nhiệm DUY NHẤT: Validate các khía cạnh của hình ảnh
    - File validation (size, extension, MIME type)
    - Image properties validation (dimensions, format)
    - Security validation (filename safety)
    - Advanced validation với thư viện bên thứ 3

    Pattern: Single Responsibility - chỉ focus vào validation
    """

    def __init__(self):
        self.max_file_size = getattr(settings, 'UPLOAD_MAX_FILE_SIZE', 5 * 1024 * 1024)  # 5MB default
        self.allowed_extensions = set(
            fmt.strip().lower() for fmt in getattr(settings, 'UPLOAD_ALLOWED_FORMATS', '.jpg,.jpeg,.png').split(",")
        )
        self.min_width = getattr(settings, 'UPLOAD_MIN_WIDTH', 100)
        self.min_height = getattr(settings, 'UPLOAD_MIN_HEIGHT', 100)

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
                logger.warning(f"Không thể khởi tạo thư viện magic: {e}")
                self.mime_validator = None
        else:
            self.mime_validator = None

    def is_safe_filename(self, filename: str) -> bool:
        """Kiểm tra filename có an toàn không"""
        if "..." in filename or "/" in filename or "\\" in filename:
            return False
        if "\x00" in filename:
            return False
        return True

    def sanitize_filename(self, filename: str) -> str:
        """Làm sạch filename"""
        filename = os.path.basename(filename)
        filename = re.sub(r"[^\w\s.-]", "", filename)
        filename = filename.replace(" ", "_")

        name, ext = os.path.splitext(filename)
        if len(name) > 100:
            name = name[:100]

        return f"{name}{ext}"

    def get_file_extension(self, filename: str) -> str:
        """Lấy file extension"""
        if not filename:
            return ""
        _, ext = os.path.splitext(filename)
        return ext.lower()

    def detect_mime(self, file_data: bytes, client_mime: Optional[str]) -> str:
        """Detect MIME type thực tế của file"""
        if self.mime_validator:
            try:
                return self.mime_validator.from_buffer(file_data)
            except Exception as e:
                logger.warning(f"[Xác thực] thư viện libmagic thất bại: {e}")
        return client_mime or "unknown"

    def check_extension_mime_consistency(
        self, ext: str, detected_mime: str
    ) -> Optional[Dict[str, Any]]:
        """Kiểm tra tính nhất quán giữa extension và MIME type"""
        expected_mime = self.ext_mime_map.get(ext)
        if expected_mime and detected_mime != "unknown":
            if detected_mime != expected_mime:
                return {
                    "success": False,
                    "error_code": FILE_INVALID_TYPE,
                    "error_message": (
                        f"Extension '{ext}' mong đợi MIME '{expected_mime}', "
                        f"nhưng phát hiện '{detected_mime}'"
                    ),
                }
        return None

    def validate_file_size(self, file_size: int) -> Dict[str, Any]:
        """Validate kích thước file"""
        if file_size > self.max_file_size:
            size_mb = self.max_file_size / (1024 * 1024)
            return {
                "success": False,
                "error_code": FILE_TOO_LARGE,
                "error_message": f"Kích thước file vượt quá kích thước tối đa cho phép ({size_mb:.2f} MB)",
            }
        return {"success": True}

    def validate_image_file_advanced(
        self, file_data: bytes, filename: str, mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            if not self.is_safe_filename(filename):
                return {
                    "success": False,
                    "error_code": FILE_UNSAFE_FILENAME,
                    "error_message": "Tên file chứa ký tự không an toàn",
                }

            file_ext = self.get_file_extension(filename)
            if file_ext not in self.allowed_extensions:
                return {
                    "success": False,
                    "error_code": FILE_INVALID_TYPE,
                    "error_message": f"Extension file '{file_ext}' không được phép. "
                    f"Được phép: {', '.join(sorted(self.allowed_extensions))}",
                }

            actual_mime_type = self.detect_mime(file_data, mime_type)

            if (
                actual_mime_type != "unknown"
                and actual_mime_type not in self.allowed_mime_types
            ):
                logger.warning(
                    f"[Xác thực] MIME không được phép: {actual_mime_type} | "
                    f"tên file={filename}, ext={file_ext}, client={mime_type}"
                )
                return {
                    "success": False,
                    "error_code": FILE_INVALID_TYPE,
                    "error_message": f"Loại MIME '{actual_mime_type}' không được phép",
                }

            mismatch = self.check_extension_mime_consistency(
                file_ext, actual_mime_type
            )
            if mismatch:
                return mismatch

            if PIL_AVAILABLE and Image is not None:
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
                            "error_message": f"Độ phân giải hình ảnh ({width}x{height}) "
                            f"thấp hơn mức tối thiểu ({self.min_width}x{self.min_height})",
                        }

                    return {
                        "success": True,
                        "file_info": {
                            "filename": self.sanitize_filename(filename),
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
                        "error_message": f"File hình ảnh bị hỏng hoặc không hợp lệ: {str(e)}",
                    }
            else:
                return {
                    "success": True,
                    "file_info": {
                        "filename": self.sanitize_filename(filename),
                        "original_filename": filename,
                        "mime_type": actual_mime_type,
                        "width": 512, 
                        "height": 512,
                        "format": "JPEG",
                    },
                }

        except Exception as e:
            logger.error(f"[Xác thực] Lỗi không mong muốn: {str(e)} | tên file={filename}")
            return {
                "success": False,
                "error_code": VALIDATION_ERROR,
                "error_message": f"Lỗi xác thực không mong muốn: {str(e)}",
            }

    def validate_file(self, file_data: bytes, filename: str, mime_type: Optional[str] = None) -> Dict[str, Any]:
        file_size = len(file_data)
        size_validation = self.validate_file_size(file_size)
        if not size_validation["success"]:
            return size_validation

        return self.validate_image_file_advanced(
            file_data=file_data,
            filename=filename,
            mime_type=mime_type
        )