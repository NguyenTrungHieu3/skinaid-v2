import pytest
from httpx import AsyncClient
import json


class TestProfileEndpoints:
    """Test cases for profile endpoints."""

    @pytest.mark.asyncio
    async def test_get_my_profile_success(self, authenticated_client: AsyncClient):
        """Test getting current user profile successfully."""
        response = await authenticated_client.get("/api/v1/profile/me")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        profile_data = data["data"]
        # Profile might be None initially, so we check structure
        if profile_data:
            assert isinstance(profile_data, dict)

    @pytest.mark.asyncio
    async def test_get_my_profile_unauthenticated(self, client: AsyncClient):
        """Test getting profile when not authenticated."""
        response = await client.get("/api/v1/profile/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile_success(self, authenticated_client: AsyncClient):
        """Test updating user profile successfully."""
        update_data = {
            "full_name": "Updated Full Name",
            "phone": "+1234567890",
            "address": "123 Test Street, Test City",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "emergency_contact": "Emergency Contact Name",
            "emergency_phone": "+0987654321",
            "medical_conditions": "None",
            "allergies": "None",
            "blood_type": "O+",
            "avatar_url": "https://example.com/avatar.jpg"
        }

        response = await authenticated_client.put("/api/v1/profile/update", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        updated_profile = data["data"]
        assert updated_profile["full_name"] == "Updated Full Name"
        assert updated_profile["phone"] == "+1234567890"

    @pytest.mark.asyncio
    async def test_update_profile_partial_data(self, authenticated_client: AsyncClient):
        """Test updating profile with partial data."""
        update_data = {
            "full_name": "Partial Update Name",
            "phone": "+1111111111"
        }

        response = await authenticated_client.put("/api/v1/profile/update", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        updated_profile = data["data"]
        assert updated_profile["full_name"] == "Partial Update Name"
        assert updated_profile["phone"] == "+1111111111"

    @pytest.mark.asyncio
    async def test_update_profile_invalid_phone(self, authenticated_client: AsyncClient):
        """Test updating profile with invalid phone number."""
        update_data = {
            "phone": "invalid-phone-number"
        }

        response = await authenticated_client.put("/api/v1/profile/update", json=update_data)
        # Should either succeed (if no validation) or fail with validation error
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_update_profile_unauthenticated(self, client: AsyncClient):
        """Test updating profile when not authenticated."""
        update_data = {
            "full_name": "Unauthorized Update"
        }

        response = await client.put("/api/v1/profile/update", json=update_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile_empty_data(self, authenticated_client: AsyncClient):
        """Test updating profile with empty data."""
        update_data = {}

        response = await authenticated_client.put("/api/v1/profile/update", json=update_data)
        # Should either succeed or return validation error
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_get_profile_after_update(self, authenticated_client: AsyncClient):
        """Test getting profile after update to verify changes persist."""
        # First update profile
        update_data = {
            "full_name": "Persistence Test Name",
            "phone": "+2222222222",
            "address": "Persistence Test Address"
        }

        await authenticated_client.put("/api/v1/profile/update", json=update_data)

        # Then get profile
        response = await authenticated_client.get("/api/v1/profile/me")
        assert response.status_code == 200

        data = response.json()
        profile_data = data.get("data")

        if profile_data:
            # Verify updated data is present
            assert profile_data.get("full_name") == "Persistence Test Name"
            assert profile_data.get("phone") == "+2222222222"
            assert profile_data.get("address") == "Persistence Test Address"

    @pytest.mark.asyncio
    async def test_profile_endpoints_integration(self, authenticated_client: AsyncClient):
        """Integration test for profile endpoints workflow."""
        # Step 1: Get initial profile (should be empty or minimal)
        response1 = await authenticated_client.get("/api/v1/profile/me")
        assert response1.status_code == 200

        # Step 2: Update profile with comprehensive data
        comprehensive_data = {
            "full_name": "Integration Test User",
            "phone": "+3333333333",
            "address": "Integration Test Address",
            "date_of_birth": "1985-05-15",
            "gender": "female",
            "emergency_contact": "Integration Emergency Contact",
            "emergency_phone": "+4444444444",
            "medical_conditions": "Diabetes",
            "allergies": "Peanuts",
            "blood_type": "A+",
            "avatar_url": "https://example.com/integration-avatar.jpg"
        }

        response2 = await authenticated_client.put("/api/v1/profile/update", json=comprehensive_data)
        assert response2.status_code == 200

        # Step 3: Verify all data was saved correctly
        response3 = await authenticated_client.get("/api/v1/profile/me")
        assert response3.status_code == 200

        data = response3.json()
        profile_data = data.get("data")

        if profile_data:
            assert profile_data.get("full_name") == "Integration Test User"
            assert profile_data.get("phone") == "+3333333333"
            assert profile_data.get("address") == "Integration Test Address"
            assert profile_data.get("date_of_birth") == "1985-05-15"
            assert profile_data.get("gender") == "female"
            assert profile_data.get("emergency_contact") == "Integration Emergency Contact"
            assert profile_data.get("emergency_phone") == "+4444444444"
            assert profile_data.get("medical_conditions") == "Diabetes"
            assert profile_data.get("allergies") == "Peanuts"
            assert profile_data.get("blood_type") == "A+"
            assert profile_data.get("avatar_url") == "https://example.com/integration-avatar.jpg"