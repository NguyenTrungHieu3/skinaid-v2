"""
Tests for Profile Controller
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.profile.controllers.profile_controllers import ProfileController
from app.modules.profile.schemas.user_profile import UserProfileUpdate, UserProfileResponse
from app.shared.schemas.response import SuccessResponse, ErrorResponse


class TestProfileController:
    """Test cases cho Profile Controller"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()

    @pytest.fixture
    def profile_controller(self, mock_db):
        """Tạo Profile controller với mock database"""
        return ProfileController(mock_db)

    @pytest.fixture
    def sample_profile_response(self):
        """Sample profile response cho testing"""
        return UserProfileResponse(
            id="test_profile_id",
            user_id="test_user_id",
            full_name="Nguyễn Văn A",
            phone="0123456789",
            date_of_birth="1990-01-01",
            gender="Nam",
            address="123 Đường ABC",
            avatar_url="https://example.com/avatar.jpg"
        )

    @pytest.mark.asyncio
    async def test_update_profile_success(self, profile_controller, sample_profile_response):
        """Test cập nhật profile thành công"""
        # Mock service methods
        profile_controller.profile_service.update_profile = AsyncMock(return_value=MagicMock())
        profile_controller.profile_service.create_profile_response = AsyncMock(return_value=sample_profile_response)

        update_data = UserProfileUpdate(full_name="Nguyễn Văn B")

        result = await profile_controller.update_profile("test_user_id", update_data)

        assert isinstance(result, SuccessResponse)
        assert result.message == "Cập nhật profile thành công"
        assert result.data.full_name == "Nguyễn Văn A"

    @pytest.mark.asyncio
    async def test_update_profile_user_not_found(self, profile_controller):
        """Test cập nhật profile với user không tồn tại"""
        from app.utils.exceptions.base_exceptions import AppBaseException
        from app.utils.constants.error_codes import USER_NOT_FOUND

        # Mock service to raise exception
        profile_controller.profile_service.update_profile = AsyncMock(
            side_effect=AppBaseException("User not found", USER_NOT_FOUND)
        )

        update_data = UserProfileUpdate(full_name="Test Name")

        result = await profile_controller.update_profile("nonexistent_user", update_data)

        assert isinstance(result, ErrorResponse)
        assert result.error_code == USER_NOT_FOUND
        assert "not found" in result.message.lower()

    @pytest.mark.asyncio
    async def test_get_profile_success(self, profile_controller, sample_profile_response):
        """Test lấy profile thành công"""
        # Mock service methods
        profile_controller.profile_service.get_profile_by_user_id = AsyncMock(return_value=MagicMock())
        profile_controller.profile_service.create_profile_response = AsyncMock(return_value=sample_profile_response)

        result = await profile_controller.get_profile("test_user_id")

        assert isinstance(result, SuccessResponse)
        assert result.message == "Lấy profile thành công"
        assert result.data.full_name == "Nguyễn Văn A"

    @pytest.mark.asyncio
    async def test_get_profile_not_found(self, profile_controller):
        """Test lấy profile khi không tìm thấy"""
        # Mock service to return None
        profile_controller.profile_service.get_profile_by_user_id = AsyncMock(return_value=None)

        result = await profile_controller.get_profile("nonexistent_user")

        assert isinstance(result, ErrorResponse)
        assert result.error_code == "PROFILE_NOT_FOUND"
        assert "không tồn tại" in result.message

    @pytest.mark.asyncio
    async def test_update_profile_invalid_data(self, profile_controller):
        """Test cập nhật profile với dữ liệu không hợp lệ"""
        from app.utils.exceptions.base_exceptions import AppBaseException
        from app.utils.constants.error_codes import USER_INVALID_DATA

        # Mock service to raise validation exception
        profile_controller.profile_service.update_profile = AsyncMock(
            side_effect=AppBaseException("Invalid data", USER_INVALID_DATA)
        )

        update_data = UserProfileUpdate()  # Empty data

        result = await profile_controller.update_profile("test_user_id", update_data)

        assert isinstance(result, ErrorResponse)
        assert result.error_code == USER_INVALID_DATA

    @pytest.mark.asyncio
    async def test_controller_internal_error(self, profile_controller):
        """Test controller xử lý lỗi internal server"""
        # Mock service to raise unexpected exception
        profile_controller.profile_service.get_profile_by_user_id = AsyncMock(
            side_effect=Exception("Unexpected database error")
        )

        result = await profile_controller.get_profile("test_user_id")

        assert isinstance(result, ErrorResponse)
        assert result.error_code == "INTERNAL_ERROR"
        assert "Có lỗi xảy ra" in result.message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])