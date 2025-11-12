import os 
import hashlib
import logging
import io
import re 
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from PIL import Image, ImageOps
from app.core.config import settings
from app.modules.audit.services.audit_service import AuditService

logger = logging.getLogger(__name__)

class UploadService: 

    ALLOWED_MIME_TYPES = {
        'image/jpeg': ['.jpg', '.jpeg'], 
        'image/png': ['.png']
    }

    MAX_FILE_SIZE = getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024)
    MIN_FILE_SIZE = getattr(settings, 'MIN_FILE_SIZE', 1024)
    MAX_IMAGE_WIDTH = getattr(settings, 'MAX_IMAGE_WIDTH', 2048)
    MAX_IMAGE_HEIGHT = getattr(settings, 'MAX_IMAGE_HEIGHT', 2048)
    MIN_IMAGE_WIDTH = getattr(settings, 'MIN_IMAGE_WIDTH', 224)
    MIN_IMAGE_HEIGHT = getattr(settings, 'MIN_IMAGE_HEIGHT', 224)
    DEFAULT_QUALITY = 85
    UPLOAD_DIR = getattr(settings, 'UPLOAD_DIR', './uploads')
    BASE_URL = getattr(settings, 'BASE_URL', 'http://localhost:8000')

    def __init__(self, audit_service: Optional[AuditService] = None):
        self.audit_service = audit_service
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        logger.info(f"Khởi tạo UploadService với thư mục lưu trữ: {self.UPLOAD_DIR}")

    
    # VALIDATION 

    def validate_file(
        self, 
        file_content: bytes, 
        file_name: str, 
        mime_type: str, 
        **kwargs
    )-> Dict[str, Any]: 
        
        errors = []
        warnings = []

        try: 

            # Kiểm tra kích thước tệp
            file_size = len(file_content)
            if file_size > self.MAX_FILE_SIZE: 
                errors.append(f"File quá lớn (max {self.MAX_FILE_SIZE // (1024*1024)}MB)")
            elif file_size < self.MIN_FILE_SIZE: 
                errors.append(f"File quá nhỏ (min {self.MIN_FILE_SIZE // 1024}KB)")

            # Kiểm tra MIME type
            if mime_type not in self.ALLOWED_MIME_TYPES: 
                errors.append(f"Chỉ hỗ trợ {', '.join(self.ALLOWED_MIME_TYPES.keys())}")
            else: 
                file_ext = Path(file_name).suffix.lower()
                allowed_exts = self.ALLOWED_MIME_TYPES[mime_type]
                if file_ext not in allowed_exts: 
                    warnings.append(f"File extension {file_ext} không khớp với MIME type")

            # Kiểm tra các điều kiện dành riêng cho ảnh
            if mime_type.startswith('image/') and not errors: 
                image_result = self._validation_image(file_content)
                errors.extend(image_result['errors'])
                warnings.extend(image_result['warnings'])

            return {
                'is_valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
        except Exception as e: 
            logger.error(f"Lỗi khi xác thực tệp: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f"Lỗi validation: {str(e)}"],
                'warnings': []
            }
    
    def _validate_image(self, file_content: bytes)->Dict[str, List[str]]: 
        errors = []
        warnings = []
        try: 
            with Image.open(io.BytesIO(file_content)) as img: 
                width, height = img.size

                if width < self.MIN_IMAGE_WIDTH or height < self.MIN_IMAGE_HEIGHT:
                    warnings.append(
                        f"Ảnh nhỏ ({width}x{height}), "
                        f"khuyến nghị tối thiểu {self.MIN_IMAGE_WIDTH}x{self.MIN_IMAGE_HEIGHT}"
                    )
                
                # Kiểm tra kích thước tối đa
                if width > self.MAX_IMAGE_WIDTH or height > self.MAX_IMAGE_HEIGHT:
                    warnings.append(
                        f"Ảnh lớn ({width}x{height}), "
                        f"sẽ được resize về {self.MAX_IMAGE_WIDTH}x{self.MAX_IMAGE_HEIGHT}"
                    )
                
                img.verify()
        except Exception as e:
            errors.append(f"Ảnh không hợp lệ: {str(e)}")
            return {'errors': errors, 'warnings': warnings}

    # IMAGE PROCESSING
    
    def process_image(
        self, 
        file_content: bytes, 
        quality: Optional[int] = None
    )-> Tuple[int, int]: 
        """
        Xử lý ảnh: resize, xoay đúng hướng, nén.
        """

        if quality is None: 
            quality = self.DEFAULT_QUALITY
        
        warnings =[]

        try:
            with Image.open(io.BytesIO(file_content)) as img: 
                original_size = img.size

                # RGB: ảnh màu, L: ảnh trắng đen 
                if img.mode not in ['RGB', 'L']: 
                    img = img.convert('RGB')
                    warnings.append("Đã convert sang RGB")
                
                if self._should_resize(original_size): 
                    new_size = self._calculate_optimal_size(original_size)
                    img.thumbnail(new_size, Image.Resampling.LANCZOS)
                
                # Điều chỉnh hướng ảnh theo EXIF (nếu có)
                img = ImageOps.exif_transpose(img)

                # Nén và chuẩn hóa sang JPEG
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=quality, optimize=True)

                processed_content = output.getvalue()

                # Ghi log tỷ lệ nén để hỗ trợ theo dõi hiệu quả lưu trữ
                original_size_bytes = len(file_content)
                final_size_bytes = len(processed_content)
                ratio = (original_size_bytes - final_size_bytes) / original_size_bytes
                
                if ratio > 0.3: 
                    warnings.append(f"Đã nén {ratio*100:.0f}%")
                
                logger.info(
                    f"Đã xử lý ảnh: {original_size} -> {img.size}, "
                    f"kích thước: {original_size_bytes} -> {final_size_bytes} "
                    f"({ratio*100:.1f}% dung lượng được tối ưu)"
                )
                
                return processed_content, warnings
        except Exception as e:
            logger.error(f"Lỗi xử lý ảnh: {str(e)}")
            raise ValueError(f"Không thể xử lý ảnh: {str(e)}")

    def _should_resize(self, current_size: Tuple[int, int]) -> bool:
        """Check if image needs resizing."""
        width, height = current_size
        return width > self.MAX_IMAGE_WIDTH or height > self.MAX_IMAGE_HEIGHT
    
    def _calculate_optimal_size(self, current_size: Tuple[int, int]) -> Tuple[int, int]:
        """Calculate optimal size maintaining aspect ratio."""
        width, height = current_size
        
        if width <= self.MAX_IMAGE_WIDTH and height <= self.MAX_IMAGE_HEIGHT:
            return current_size
        
        if width > height:
            new_width = min(width, self.MAX_IMAGE_WIDTH)
            new_height = int(height * new_width / width)
        else:
            new_height = min(height, self.MAX_IMAGE_HEIGHT)
            new_width = int(width * new_height / height)
        
        return (new_width, new_height)
    
    # STORAGE 

    def save_to_storage(
        self,
        file_content: bytes,
        file_path: str
    ) -> str:
        """
        Lưu tệp vào bộ nhớ cục bộ của máy chủ.
        """
        try:
            # Chuẩn hóa đường dẫn để tránh tấn công path traversal
            safe_path = self._sanitize_path(file_path)
            
            # Tạo đường dẫn đầy đủ
            full_path = Path(self.UPLOAD_DIR) / safe_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Ghi dữ liệu tệp xuống ổ đĩa
            with open(full_path, 'wb') as f:
                f.write(file_content)
            
            # Tạo URL công khai để truy cập tệp
            file_url = f"{self.BASE_URL}/uploads/{safe_path}"
            
            logger.info(f"Đã lưu tệp tại: {full_path}")
            return file_url
            
        except Exception as e:
            logger.error(f"Lưu tệp thất bại: {str(e)}")
            raise ValueError(f"Không thể lưu file: {str(e)}")
    
    def _sanitize_path(self, file_path: str) -> str:
        """Chuẩn hóa đường dẫn tệp để ngăn chặn tấn công path traversal."""
        # Loại bỏ ../ và ..\
        safe_path = re.sub(r'\.\.[/\\]', '', file_path)
        
        # Loại bỏ dấu / hoặc \ ở đầu
        safe_path = safe_path.lstrip('/\\')
        
        # Chuẩn hóa đường dẫn
        safe_path = os.path.normpath(safe_path)
        
        # Đảm bảo đường dẫn không thoát ra ngoài thư mục cho phép
        if safe_path.startswith('..'):
            raise ValueError("Invalid file path")
        
        return safe_path
    
    # UTILITIES

    def generate_file_path(
        self,
        mime_type: str,
        user_id: Optional[str] = None,
        purpose: str = "general"
    ) -> str:
        """
        Sinh đường dẫn lưu trữ duy nhất cho tệp.

        Định dạng:
        - User: users/{user_id}/{purpose}/{timestamp}_{uuid}.jpg
        - Guest: guest/{timestamp}_{uuid}.jpg
        """
        unique_id = str(uuid4())[:8]  # UUID rút gọn
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = self._get_extension_for_mime_type(mime_type)
        
        if user_id:
            return f"users/{user_id}/{purpose}/{timestamp}_{unique_id}{file_ext}"
        else:
            return f"guest/{timestamp}_{unique_id}{file_ext}"
    
    def _get_extension_for_mime_type(self, mime_type: str) -> str:
        return '.jpg'
    
    def calculate_checksum(self, file_content: bytes) -> str:
        return hashlib.sha256(file_content).hexdigest()
    
    # MAIN UPLOAD METHOD
    
    async def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        mime_type: str,
        user_id: Optional[str] = None,
        purpose: str = "general",
        quality: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Hàm xử lý upload chính: xác thực, xử lý ảnh, lưu trữ, ghi log.
        """
        try:
            # === BƯỚC 1: XÁC THỰC TỆP ===
            
            validation_result = self.validate_file(
                file_content=file_content,
                file_name=file_name,
                mime_type=mime_type
            )
            
            if not validation_result['is_valid']:
                if self.audit_service:
                    await self.audit_service.log_file_upload(
                        user_id=user_id,
                        file_name=file_name,
                        file_size=len(file_content),
                        success=False,
                        error_message="; ".join(validation_result['errors']),
                        is_guest=(user_id is None),
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                
                raise ValueError("; ".join(validation_result['errors']))
            
            all_warnings = validation_result.get('warnings', [])
            
            # === BƯỚC 2: XỬ LÝ ẢNH (NẾU LÀ ẢNH) ===
            
            processed_content = file_content
            final_mime_type = mime_type
            
            if mime_type.startswith('image/'):
                processed_content, process_warnings = self.process_image(
                    file_content=file_content,
                    quality=quality
                )
                all_warnings.extend(process_warnings)
                final_mime_type = 'image/jpeg'  # Always JPEG after processing
            
            final_size = len(processed_content)
            
            # === BƯỚC 3: SINH ĐƯỜNG DẪN VÀ LƯU TỆP ===
            
            file_path = self.generate_file_path(
                mime_type=final_mime_type,
                user_id=user_id,
                purpose=purpose
            )
            
            file_url = self.save_to_storage(
                file_content=processed_content,
                file_path=file_path
            )
            
            # === BƯỚC 4: TÍNH CHECKSUM ===
            
            checksum = self.calculate_checksum(processed_content)
            
            # === BƯỚC 5: GHI NHẬT KÝ KIỂM TOÁN (THÀNH CÔNG) ===
            
            if self.audit_service:
                await self.audit_service.log_file_upload(
                    user_id=user_id,
                    file_path=file_path,
                    file_name=file_name,
                    file_size=final_size,
                    success=True,
                    is_guest=(user_id is None),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details={
                        'original_size': len(file_content),
                        'final_size': final_size,
                        'mime_type': final_mime_type,
                        'purpose': purpose,
                        'warnings': all_warnings
                    }
                )
            
            # === BƯỚC 6: XÂY DỰNG PHẢN HỒI ===
            
            logger.info(
                f"Tải lên thành công: {file_name} -> {Path(file_path).name} "
                f"({len(file_content)} -> {final_size} bytes)"
            )
            
            return {
                'file_url': file_url,
                'file_name': Path(file_path).name,
                'file_size': final_size,
                'mime_type': final_mime_type,
                'checksum': checksum,
                'warnings': all_warnings if all_warnings else None
            }
            
        except ValueError:
            # Ném lại lỗi xác thực để tầng trên xử lý
            raise

        except Exception as e:
            # Ghi log các lỗi không mong đợi trong quá trình upload
            logger.error(f"Tải lên thất bại: {file_name} - {str(e)}")
            
            if self.audit_service:
                await self.audit_service.log_file_upload(
                    user_id=user_id,
                    file_name=file_name,
                    file_size=len(file_content),
                    success=False,
                    error_message=str(e),
                    is_guest=(user_id is None),
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            raise ValueError(f"Tải lên thất bại: {str(e)}")