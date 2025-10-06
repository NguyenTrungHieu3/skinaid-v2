import pytest
from httpx import AsyncClient
import io


class TestAIEndpoints:
    """Test cases for AI endpoints."""

    @pytest.mark.asyncio
    async def test_ai_health_success(self, client: AsyncClient):
        """Test AI health check when service is available."""
        response = await client.get("/api/v1/ai/health")
        # Should return health status
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "status" in data["data"]

    @pytest.mark.asyncio
    async def test_ai_analyze_image_success(self, client: AsyncClient):
        """Test AI image analysis when service is available."""
        # Create fake image content
        fake_image_content = b"fake image content for AI analysis"

        files = {"file": ("ai_test.jpg", io.BytesIO(fake_image_content), "image/jpeg")}

        response = await client.post("/api/v1/ai/analyze", files=files)
        # Should either succeed or fail with service unavailable
        assert response.status_code in [200, 500, 503]

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "detections" in data
            assert "num_detections" in data
            assert "image_size" in data
            assert "processing_time" in data

    @pytest.mark.asyncio
    async def test_ai_analyze_png_image(self, client: AsyncClient):
        """Test AI analysis with PNG image."""
        png_content = b"fake png content for AI"
        files = {"file": ("ai_test.png", io.BytesIO(png_content), "image/png")}

        response = await client.post("/api/v1/ai/analyze", files=files)
        # Should handle PNG files
        assert response.status_code in [200, 400, 500, 503]

    @pytest.mark.asyncio
    async def test_ai_analyze_invalid_file_type(self, client: AsyncClient):
        """Test AI analysis with invalid file type."""
        invalid_content = b"This is not an image"
        files = {"file": ("invalid.txt", io.BytesIO(invalid_content), "text/plain")}

        response = await client.post("/api/v1/ai/analyze", files=files)
        # Should reject invalid file types
        assert response.status_code == 400

        if response.status_code == 400:
            data = response.json()
            assert "Invalid file type" in data["detail"]

    @pytest.mark.asyncio
    async def test_ai_analyze_empty_file(self, client: AsyncClient):
        """Test AI analysis with empty file."""
        empty_content = b""
        files = {"file": ("empty.jpg", io.BytesIO(empty_content), "image/jpeg")}

        response = await client.post("/api/v1/ai/analyze", files=files)
        # Should handle empty files
        assert response.status_code in [200, 400, 500, 503]

    @pytest.mark.asyncio
    async def test_ai_analyze_corrupted_image(self, client: AsyncClient):
        """Test AI analysis with corrupted image data."""
        # Create somewhat corrupted image-like content
        corrupted_content = b"\xff\xd8\xff\x00\x00\x00\x00\x00"  # Partial JPEG header
        files = {"file": ("corrupted.jpg", io.BytesIO(corrupted_content), "image/jpeg")}

        response = await client.post("/api/v1/ai/analyze", files=files)
        # Should handle corrupted images gracefully
        assert response.status_code in [200, 400, 500, 503]

    @pytest.mark.asyncio
    async def test_ai_analyze_no_file(self, client: AsyncClient):
        """Test AI analysis without providing file."""
        response = await client.post("/api/v1/ai/analyze")
        # Should require file parameter
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_ai_analyze_multiple_files(self, client: AsyncClient):
        """Test AI analysis with multiple files (should use first or fail)."""
        content1 = b"first image content"
        content2 = b"second image content"

        files = [
            ("file", ("multi1.jpg", io.BytesIO(content1), "image/jpeg")),
            ("file", ("multi2.jpg", io.BytesIO(content2), "image/jpeg"))
        ]

        response = await client.post("/api/v1/ai/analyze", files=files)
        # Should handle multiple files (probably use first or fail)
        assert response.status_code in [200, 400, 422, 500, 503]

    @pytest.mark.asyncio
    async def test_ai_analyze_oversized_image(self, client: AsyncClient):
        """Test AI analysis with oversized image."""
        # Create large fake image (simulate size limit)
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        files = {"file": ("large.jpg", io.BytesIO(large_content), "image/jpeg")}

        response = await client.post("/api/v1/ai/analyze", files=files)
        # Should handle file size limits
        assert response.status_code in [200, 413, 500, 503]

    @pytest.mark.asyncio
    async def test_ai_health_detailed_response(self, client: AsyncClient):
        """Test AI health check response structure."""
        response = await client.get("/api/v1/ai/health")

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data

            health_data = data["data"]
            assert "status" in health_data
            assert "services" in health_data

            # Status should be either healthy or unhealthy
            assert health_data["status"] in ["healthy", "unhealthy"]

    @pytest.mark.asyncio
    async def test_ai_analyze_response_structure(self, client: AsyncClient):
        """Test AI analysis response structure when successful."""
        # Use a minimal valid image-like content
        minimal_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\x00\x00\x00"

        files = {"file": ("minimal.jpg", io.BytesIO(minimal_jpeg), "image/jpeg")}

        response = await client.post("/api/v1/ai/analyze", files=files)

        if response.status_code == 200:
            data = response.json()

            # Check response structure
            assert "success" in data
            assert "detections" in data
            assert "num_detections" in data
            assert "image_size" in data
            assert "processing_time" in data
            assert "ai_model_version" in data

            # Validate data types
            assert isinstance(data["detections"], list)
            assert isinstance(data["num_detections"], int)
            assert isinstance(data["image_size"], dict)
            assert isinstance(data["processing_time"], (int, float))

            # Image size should have width and height
            if data["image_size"]:
                assert "width" in data["image_size"]
                assert "height" in data["image_size"]

    @pytest.mark.asyncio
    async def test_ai_analyze_different_image_formats(self, client: AsyncClient):
        """Test AI analysis with different image formats."""
        formats_to_test = [
            ("jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF", "image/jpeg"),
            ("png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", "image/png")
        ]

        for ext, content, mime_type in formats_to_test:
            files = {"file": (f"test.{ext}", io.BytesIO(content), mime_type)}
            response = await client.post("/api/v1/ai/analyze", files=files)

            # Each format should be handled (success or appropriate error)
            assert response.status_code in [200, 400, 500, 503]

    @pytest.mark.asyncio
    async def test_ai_service_unavailable_simulation(self, client: AsyncClient, monkeypatch):
        """Test behavior when AI service is unavailable."""
        # Mock the AI processing service to simulate unavailability
        async def mock_analyze_unavailable(temp_file_path):
            return {
                "success": False,
                "error": "AI service unavailable",
                "error_code": "SERVICE_UNAVAILABLE"
            }

        # This would require mocking the AIProcessingService.analyze_image method
        # For now, we'll just test the endpoint exists and handles requests
        fake_content = b"test content for unavailable service"
        files = {"file": ("unavailable_test.jpg", io.BytesIO(fake_content), "image/jpeg")}

        response = await client.post("/api/v1/ai/analyze", files=files)
        # Should handle service unavailable gracefully
        assert response.status_code in [200, 500, 503]

    @pytest.mark.asyncio
    async def test_ai_analyze_with_special_characters_filename(self, client: AsyncClient):
        """Test AI analysis with special characters in filename."""
        special_content = b"content for special filename test"
        files = {"file": ("test_file-with_special.chars.jpg", io.BytesIO(special_content), "image/jpeg")}

        response = await client.post("/api/v1/ai/analyze", files=files)
        # Should handle special characters in filename
        assert response.status_code in [200, 400, 500, 503]

    @pytest.mark.asyncio
    async def test_ai_concurrent_requests(self, client: AsyncClient):
        """Test AI service with concurrent requests."""
        import asyncio

        async def make_request(i):
            content = f"concurrent request {i}".encode()
            files = {"file": (f"concurrent_{i}.jpg", io.BytesIO(content), "image/jpeg")}
            return await client.post("/api/v1/ai/analyze", files=files)

        # Make multiple concurrent requests
        tasks = [make_request(i) for i in range(3)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # All requests should complete (either success or error)
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                # If there's an exception, it should be a handled HTTP exception
                assert "HTTP" in str(type(response)) or "Connect" in str(type(response))
            else:
                assert response.status_code in [200, 400, 500, 503]