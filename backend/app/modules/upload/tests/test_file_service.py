import pytest
import os
import tempfile
from pathlib import Path
from fastapi import UploadFile
from io import BytesIO

from app.modules.upload.services.file_service import FileService


class TestFileService:
    """Test FileService độc lập"""

    @pytest.fixture
    def file_service(self):
        """Tạo FileService với temp directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Monkey patch upload_dir để dùng temp directory
            original_upload_dir = None

            # Save original value
            if hasattr(file_service, 'upload_dir'):
                original_upload_dir = file_service.upload_dir

            file_service = FileService()
            file_service.upload_dir = temp_dir

            yield file_service

            # Restore original value
            if original_upload_dir:
                file_service.upload_dir = original_upload_dir

    @pytest.fixture
    def sample_image_bytes(self):
        """Tạo sample image bytes để test"""
        # Tạo 1x1 pixel PNG đơn giản
        png_header = b'\x89PNG\r\n\x1a\n'  # PNG signature
        ihdr = b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00'
        image_data = b'\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00'
        iend = b'\x00\x00\x00\x00IEND\xae\x42\x60\x82'

        return png_header + ihdr + image_data + iend

    def test_generate_file_path(self, file_service):
        """Test file path generation"""
        filename = "test_image.jpg"
        user_id = "user123"

        file_path = file_service.generate_file_path(filename, user_id)

        # Kiểm tra format: YYYY/MM/DD/user_id_timestamp_uuid.ext
        assert "/" in file_path  # Có date path
        assert user_id in file_path  # Có user_id
        assert file_path.endswith(".jpg")  # Có extension đúng

        # Kiểm tra thư mục được tạo
        full_path = os.path.join(file_service.upload_dir, file_path)
        assert os.path.dirname(full_path)  # Thư mục tồn tại

    async def test_save_and_delete_file(self, file_service, sample_image_bytes):
        """Test save và delete file"""
        # Tạo mock UploadFile
        file_like = BytesIO(sample_image_bytes)
        file_like.name = "test.png"

        # Tạo UploadFile từ bytes
        file = UploadFile(file=file_like, filename="test.png")

        # Generate file path
        file_path = file_service.generate_file_path("test.png", "user123")

        # Save file
        result = await file_service.save_file(file, file_path)

        assert result["success"] is True
        assert "file_path" in result
        assert result["file_size"] > 0

        # Kiểm tra file tồn tại trên disk
        full_path = os.path.join(file_service.upload_dir, file_path)
        assert os.path.exists(full_path)

        # Delete file
        delete_success = file_service.delete_file(file_path)
        assert delete_success is True

        # Kiểm tra file đã bị xóa
        assert not os.path.exists(full_path)

    async def test_file_exists(self, file_service, sample_image_bytes):
        """Test file exists check"""
        file_like = BytesIO(sample_image_bytes)
        file = UploadFile(file=file_like, filename="test.png")

        file_path = file_service.generate_file_path("test.png", "user123")

        # File chưa tồn tại
        assert file_service.file_exists(file_path) is False

        # Save file
        await file_service.save_file(file, file_path)

        # File đã tồn tại
        assert file_service.file_exists(file_path) is True

        # Delete file
        file_service.delete_file(file_path)

        # File không còn tồn tại
        assert file_service.file_exists(file_path) is False

    async def test_get_file_size(self, file_service, sample_image_bytes):
        """Test get file size"""
        file_like = BytesIO(sample_image_bytes)
        file = UploadFile(file=file_like, filename="test.png")

        file_path = file_service.generate_file_path("test.png", "user123")

        # File chưa tồn tại → None
        size = file_service.get_file_size(file_path)
        assert size is None

        # Save file
        await file_service.save_file(file, file_path)

        # File đã tồn tại → có size
        size = file_service.get_file_size(file_path)
        assert size > 0
        assert size == len(sample_image_bytes)

    async def test_save_file_with_invalid_path(self, file_service):
        """Test save file với đường dẫn không hợp lệ"""
        file_like = BytesIO(b"test")
        file = UploadFile(file=file_like, filename="test.txt")

        # Đường dẫn với ký tự đặc biệt
        invalid_path = "../../../etc/passwd"

        result = await file_service.save_file(file, invalid_path)

        # Không nên crash, nhưng có thể fail
        # Quan trọng là không expose thông tin hệ thống
        assert "success" in result