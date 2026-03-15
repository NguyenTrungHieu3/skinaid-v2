from pathlib import Path
from uuid import uuid4
from datetime import datetime
from typing import Optional
from fastapi import UploadFile
import aiofiles
import os

from app.core.config import settings

class FileService: 
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        ext = Path(original_filename).suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid4())[:8]
        return f"{timestamp}_{unique_id}{ext}"
    

    @staticmethod
    async def save_file(
        file_content: bytes,
        filename: str, 
        subfolder: str = "uploads"
    )-> dict: 
        # tạo folder nếu không có
        upload_dir = Path(settings.UPLOAD_DIR)/ subfolder
        upload_dir.mkdir(parents=True, exist_ok=True)

        # tạo filename
        unique_filename = FileService.generate_unique_filename(filename)
        file_path = upload_dir / unique_filename

        async with aiofiles.open(file_path, 'wb') as f: 
            await f.write(file_content)

        file_url = f"/uploads/{subfolder}/{unique_filename}"

        return {
            'file_path': str(file_path),
            'file_url': file_url,
            'filename': unique_filename
        }
    
    @staticmethod
    async def delete_file(file_path: str)-> bool:
        try: 
            if os.path.exists(file_path): 
                os.remove(file_path)
                return True
            return False
        except Exception as e: 
            print(f"Error deleting file {file_path}: {e}")
            return False
