from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
import filetype
from PIL import Image
from io import BytesIO

from app.core.config import settings

class FileValidator: 
    
    @staticmethod 
    async def validate_upload_file(
        file: UploadFile, 
        max_size: Optional[int] = None, 
        allowed_types: Optional[list] = None, 
        min_dimensions: Optional[tuple] = None, 
        max_dimensions: Optional[tuple] = None
    )-> dict: 
        """Validate uploaded file"""

        # SIZE validations
        file_content = await file.read()
        file_size = len(file_content)
        max_size = max_size or settings.MAX_UPLOAD_SIZE

        if file_size > max_size:
            return {
                'valid': False, 
                'error': f'file quá lớn. Tối đa{max_size/1024*1024} MB'
            }
        
        if file_size < settings.MIN_FILE_SIZE: 
            return {
                'valid': False,
                'error': f'File quá nhỏ. Tối thiểu {settings.MIN_FILE_SIZE}B'
            }
        
        # MIME validation using filetype
        kind = filetype.guess(file_content)
        if kind is None:
            return {
                'valid': False,
                'error': 'Không thể xác định loại file'
            }
        
        mime = kind.mime
        allowed_types = allowed_types or ['image/jpeg', 'image/jpg', 'image/png']

        if mime not in allowed_types:
            return {
                'valid': False,
                'error': f'Định dạng không được hỗ trợ. Chỉ chấp nhận: {", ".join(allowed_types)}'
            }
        
        #  IMAGE dimensions validation
        dimensions = None
        try:
            image = Image.open(BytesIO(file_content))
            width, height = image.size
            dimensions = (width, height)

            min_w = min_dimensions[0] if min_dimensions else settings.MIN_IMAGE_WIDTH
            min_h = min_dimensions[1] if min_dimensions else settings.MIN_IMAGE_HEIGHT
            max_w = max_dimensions[0] if max_dimensions else settings.MAX_IMAGE_WIDTH
            max_h = max_dimensions[1] if max_dimensions else settings.MAX_IMAGE_HEIGHT

            # Debug logging
            print(f"[FILE_VALIDATOR] Image dimensions: {width}x{height}")
            print(f"[FILE_VALIDATOR] Min allowed: {min_w}x{min_h}")
            print(f"[FILE_VALIDATOR] Max allowed: {max_w}x{max_h}")
            print(f"[FILE_VALIDATOR] Settings values - MIN: {settings.MIN_IMAGE_WIDTH}x{settings.MIN_IMAGE_HEIGHT}, MAX: {settings.MAX_IMAGE_WIDTH}x{settings.MAX_IMAGE_HEIGHT}")

            if width < min_w or height < min_h:
                return {
                    'valid': False,
                    'error': f'Kích thước ảnh quá nhỏ. Tối thiểu {min_w}x{min_h}px. Ảnh của bạn: {width}x{height}px'
                }
            
            if width > max_w or height > max_h:
                return {
                    'valid': False,
                    'error': f'Kích thước ảnh quá lớn. Tối đa {max_w}x{max_h}px. Ảnh của bạn: {width}x{height}px'
                }
        
        except Exception as e:
            return {
                'valid': False,
                'error': f'Không thể đọc ảnh: {str(e)}'
            }
        
        await file.seek(0)
        
        return {
            'valid': True,
            'error': None,
            'mime_type': mime,
            'size': file_size,
            'dimensions': dimensions,
            'content': file_content
        }