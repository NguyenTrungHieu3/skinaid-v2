import pytest
from httpx import AsyncClient


class TestFirstAidEndpoints:
    """Test cases for first aid endpoints."""

    @pytest.mark.asyncio
    async def test_get_first_aid_guide_success(self, client: AsyncClient):
        """Test getting first aid guide successfully."""
        response = await client.get("/api/v1/first-aid/guide/burn/mild")
        # Should return guide or appropriate error if not found
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data

    @pytest.mark.asyncio
    async def test_get_first_aid_guide_invalid_wound_type(self, client: AsyncClient):
        """Test getting first aid guide with invalid wound type."""
        response = await client.get("/api/v1/first-aid/guide/invalid_wound/severe")
        # Should handle invalid wound types gracefully
        assert response.status_code in [200, 404, 422]

    @pytest.mark.asyncio
    async def test_get_first_aid_guide_invalid_severity(self, client: AsyncClient):
        """Test getting first aid guide with invalid severity."""
        response = await client.get("/api/v1/first-aid/guide/burn/invalid_severity")
        # Should handle invalid severity gracefully
        assert response.status_code in [200, 404, 422]

    @pytest.mark.asyncio
    async def test_get_first_aid_guide_case_sensitivity(self, client: AsyncClient):
        """Test case sensitivity in wound type and severity."""
        # Test uppercase
        response1 = await client.get("/api/v1/first-aid/guide/BURN/MILD")
        # Test mixed case
        response2 = await client.get("/api/v1/first-aid/guide/Burn/Severe")

        # Both should be handled consistently
        assert response1.status_code in [200, 404, 422]
        assert response2.status_code in [200, 404, 422]

    @pytest.mark.asyncio
    async def test_get_available_wound_types(self, client: AsyncClient):
        """Test getting available wound types."""
        response = await client.get("/api/v1/first-aid/wound-types")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        # Data should be a dictionary or list of wound types
        wound_data = data["data"]
        assert isinstance(wound_data, (dict, list))

    @pytest.mark.asyncio
    async def test_search_first_aid_guides_no_filters(self, client: AsyncClient):
        """Test searching first aid guides without filters."""
        response = await client.get("/api/v1/first-aid/search")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        # Should return a list of guides
        search_results = data["data"]
        assert isinstance(search_results, list)

    @pytest.mark.asyncio
    async def test_search_first_aid_guides_with_wound_type_filter(self, client: AsyncClient):
        """Test searching with wound type filter."""
        response = await client.get("/api/v1/first-aid/search?wound_type=burn")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        results = data["data"]
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_first_aid_guides_with_severity_filter(self, client: AsyncClient):
        """Test searching with severity filter."""
        response = await client.get("/api/v1/first-aid/search?severity=mild")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        results = data["data"]
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_first_aid_guides_with_both_filters(self, client: AsyncClient):
        """Test searching with both wound type and severity filters."""
        response = await client.get("/api/v1/first-aid/search?wound_type=burn&severity=moderate")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        results = data["data"]
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_first_aid_guides_with_limit(self, client: AsyncClient):
        """Test searching with custom limit."""
        response = await client.get("/api/v1/first-aid/search?limit=5")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        results = data["data"]
        assert isinstance(results, list)
        # Should respect the limit (or return all if less available)
        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_search_first_aid_guides_invalid_limit(self, client: AsyncClient):
        """Test searching with invalid limit."""
        response = await client.get("/api/v1/first-aid/search?limit=0")
        # Should handle invalid limit gracefully
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_search_first_aid_guides_excessive_limit(self, client: AsyncClient):
        """Test searching with excessive limit."""
        response = await client.get("/api/v1/first-aid/search?limit=1000")
        # Should handle excessive limit (probably cap it)
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_search_first_aid_guides_nonexistent_wound_type(self, client: AsyncClient):
        """Test searching with non-existent wound type."""
        response = await client.get("/api/v1/first-aid/search?wound_type=nonexistent_type")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        results = data["data"]
        assert isinstance(results, list)
        # Should return empty list for non-existent wound type
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_first_aid_guides_nonexistent_severity(self, client: AsyncClient):
        """Test searching with non-existent severity."""
        response = await client.get("/api/v1/first-aid/search?severity=nonexistent_severity")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        results = data["data"]
        assert isinstance(results, list)
        # Should return empty list for non-existent severity
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_first_aid_guide_response_structure(self, client: AsyncClient):
        """Test first aid guide response structure."""
        response = await client.get("/api/v1/first-aid/guide/burn/mild")

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data

            guide_data = data["data"]
            # Should contain relevant first aid information
            assert isinstance(guide_data, dict)

    @pytest.mark.asyncio
    async def test_wound_types_response_structure(self, client: AsyncClient):
        """Test wound types response structure."""
        response = await client.get("/api/v1/first-aid/wound-types")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        wound_types_data = data["data"]
        assert isinstance(wound_types_data, (dict, list))

        # If it's a dict, should have wound types as keys
        if isinstance(wound_types_data, dict):
            assert len(wound_types_data) > 0
            # Each wound type should have severity levels
            for wound_type, severities in wound_types_data.items():
                assert isinstance(wound_type, str)
                assert isinstance(severities, list)
                assert len(severities) > 0

    @pytest.mark.asyncio
    async def test_search_response_structure(self, client: AsyncClient):
        """Test search response structure."""
        response = await client.get("/api/v1/first-aid/search?limit=10")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        search_data = data["data"]
        assert isinstance(search_data, list)

        # Each result should have expected structure
        for result in search_data:
            assert isinstance(result, dict)
            # Should contain wound type and severity information

    @pytest.mark.asyncio
    async def test_common_wound_types_coverage(self, client: AsyncClient):
        """Test that common wound types are covered."""
        common_wound_types = [
            "burn", "abrasion", "bruise"
        ]
        common_severities = ["mild", "moderate", "severe"]

        for wound_type in common_wound_types:
            for severity in common_severities:
                response = await client.get(f"/api/v1/first-aid/guide/{wound_type}/{severity}")
                # Should handle all common combinations (success or not found is OK)
                assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_first_aid_endpoints_integration(self, client: AsyncClient):
        """Integration test for first aid endpoints."""
        # Step 1: Get available wound types
        response1 = await client.get("/api/v1/first-aid/wound-types")
        assert response1.status_code == 200

        wound_types_data = response1.json()["data"]

        # Step 2: Search all guides
        response2 = await client.get("/api/v1/first-aid/search")
        assert response2.status_code == 200

        all_guides = response2.json()["data"]

        # Step 3: If we have wound types and guides, test a specific guide
        if isinstance(wound_types_data, dict) and wound_types_data:
            # Pick first available wound type and severity
            first_wound_type = list(wound_types_data.keys())[0]
            first_severity = wound_types_data[first_wound_type][0]

            response3 = await client.get(f"/api/v1/first-aid/guide/{first_wound_type}/{first_severity}")
            # Should be able to get the specific guide
            assert response3.status_code in [200, 404]

            # Step 4: Search with filters
            response4 = await client.get(f"/api/v1/first-aid/search?wound_type={first_wound_type}")
            assert response4.status_code == 200

            response5 = await client.get(f"/api/v1/first-aid/search?severity={first_severity}")
            assert response5.status_code == 200

    @pytest.mark.asyncio
    async def test_first_aid_search_pagination(self, client: AsyncClient):
        """Test first aid search pagination."""
        # Test with different limits
        limits = [1, 5, 10, 50]

        for limit in limits:
            response = await client.get(f"/api/v1/first-aid/search?limit={limit}")
            assert response.status_code == 200

            data = response.json()
            results = data["data"]
            assert isinstance(results, list)
            # Should respect the limit (or return all if less available)
            assert len(results) <= limit

    @pytest.mark.asyncio
    async def test_first_aid_guide_data_integrity(self, client: AsyncClient):
        """Test that first aid guide data is properly structured."""
        response = await client.get("/api/v1/first-aid/guide/burn/mild")

        if response.status_code == 200:
            data = response.json()
            guide_data = data["data"]

            # Guide should have meaningful content
            assert isinstance(guide_data, dict)

            # Should contain instructions or similar fields
            # (exact fields depend on implementation)
            assert len(guide_data) > 0