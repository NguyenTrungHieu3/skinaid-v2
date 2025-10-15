"""
Tests for Profile Service
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.modules.profile.services.profile_service import ProfileService
from app.modules.profile.schemas.user_profile import UserProfileUpdate, UserProfileResponse


class TestProfileService:
    """Test cases cho Profile Service"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()

    @pytest.fixture
    def profile_service(self, mock_db):
        """Tạo Profile service với mock database"""
        return ProfileService(mock_db)

    @pytest.fixture
    def sample_profile_data(self):
        """Sample profile data cho testing"""
        return {
            "id": "test_profile_id",
            "user_id": "test_user_id",
            "full_name": "Nguyễn Văn A",
            "phone": "0123456789",
            "date_of_birth": "1990-01-01",
            "gender": "Nam",
            "address": "123 Đường ABC, TP.HCM",
            "avatar_url": "https://example.com/avatar.jpg",
            "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
            "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
        }

    @pytest.mark.asyncio
    async def test_update_profile_success(self, profile_service, sample_profile_data):
        """Test cập nhật profile thành công"""
        # Mock database operations
        mock_result = AsyncMock()
        mock_result.mappings.return_value.first.return_value = sample_profile_data

        profile_service.db.execute = AsyncMock(return_value=mock_result)
        profile_service.db.commit = AsyncMock()

        # Test data
        user_id = "test_user_id"
        update_data = UserProfileUpdate(
            full_name="Nguyễn Văn B",
            phone="0987654321"
        )

        result = await profile_service.update_profile(user_id, update_data)

        assert result is not None
        profile_service.db.execute.assert_called()
        profile_service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_profile_by_user_id_success(self, profile_service, sample_profile_data):
        """Test lấy profile theo user_id thành công"""
        mock_result = AsyncMock()
        mock_result.mappings.return_value.first.return_value = sample_profile_data

        profile_service.db.execute = AsyncMock(return_value=mock_result)

        result = await profile_service.get_profile_by_user_id("test_user_id")

        assert result is not None
        assert result.profile_id == "test_profile_id"

    @pytest.mark.asyncio
    async def test_get_profile_by_user_id_not_found(self, profile_service):
        """Test lấy profile khi không tìm thấy"""
        mock_result = AsyncMock()
        mock_result.mappings.return_value.first.return_value = None

        profile_service.db.execute = AsyncMock(return_value=mock_result)

        result = await profile_service.get_profile_by_user_id("nonexistent_user")

        assert result is None

    @pytest.mark.asyncio
    async def test_create_profile_response_success(self, profile_service, sample_profile_data):
        """Test tạo profile response thành công"""
        result = await profile_service.create_profile_response(sample_profile_data)

        assert isinstance(result, UserProfileResponse)
        assert result.full_name == "Nguyễn Văn A"
        assert result.phone == "0123456789"

    @pytest.mark.asyncio
    async def test_update_profile_database_error(self, profile_service):
        """Test cập nhật profile với lỗi database"""
        profile_service.db.execute = AsyncMock(side_effect=Exception("Database error"))

        update_data = UserProfileUpdate(full_name="Test Name")

        with pytest.raises(Exception):
            await profile_service.update_profile("test_user_id", update_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])