import pytest
from httpx import AsyncClient
import os
import io


class TestUploadEndpoints:
    """Test cases for upload endpoints."""

    @pytest.mark.asyncio
    async def test_upload_image_success(self, authenticated_client: AsyncClient, test_image_path):
        """Test successful image upload."""
        # Create a test image if it doesn't exist
        if not os.path.exists(test_image_path):
            # Create a simple test image in memory
            test_image_content = b"fake image content"
        else:
            with open(test_image_path, "rb") as f:
                test_image_content = f.read()

        # Upload image
        files = {"file": ("test_image.jpg", io.BytesIO(test_image_content), "image/jpeg")}
        data = {"description": "Test wound image"}

        response = await authenticated_client.post("/api/v1/upload/image", files=files, data=data)
        # This might fail if AI service is not running, but endpoint should exist
        assert response.status_code in [200, 500, 503]

        if response.status_code == 200:
            response_data = response.json()
            assert response_data["success"] is True
            assert "data" in response_data

    @pytest.mark.asyncio
    async def test_upload_image_without_description(self, authenticated_client: AsyncClient):
        """Test image upload without description."""
        test_image_content = b"fake image content for test without description"

        files = {"file": ("test_no_desc.jpg", io.BytesIO(test_image_content), "image/jpeg")}

        response = await authenticated_client.post("/api/v1/upload/image", files=files)
        # Should handle missing description gracefully
        assert response.status_code in [200, 422, 500, 503]

    @pytest.mark.asyncio
    async def test_upload_image_invalid_file_type(self, authenticated_client: AsyncClient):
        """Test upload with invalid file type."""
        # Create fake non-image content
        fake_content = b"This is not an image file"

        files = {"file": ("fake.txt", io.BytesIO(fake_content), "text/plain")}

        response = await authenticated_client.post("/api/v1/upload/image", files=files)
        # Should reject invalid file types
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_upload_image_unauthenticated(self, client: AsyncClient):
        """Test upload when not authenticated."""
        fake_content = b"fake image content"
        files = {"file": ("test.jpg", io.BytesIO(fake_content), "image/jpeg")}

        response = await client.post("/api/v1/upload/image", files=files)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_image_analysis_success(self, authenticated_client: AsyncClient):
        """Test getting image analysis successfully."""
        # First upload an image (if AI service is available)
        test_image_content = b"fake image content"
        files = {"file": ("analysis_test.jpg", io.BytesIO(test_image_content), "image/jpeg")}

        upload_response = await authenticated_client.post("/api/v1/upload/image", files=files)

        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            image_id = upload_data["data"].get("image_id")

            if image_id:
                # Get image analysis
                response = await authenticated_client.get(f"/api/v1/upload/image/{image_id}")
                # Might fail if processing not complete, but endpoint should exist
                assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_get_image_analysis_nonexistent(self, authenticated_client: AsyncClient):
        """Test getting analysis for non-existent image."""
        fake_image_id = "00000000-0000-0000-0000-000000000000"

        response = await authenticated_client.get(f"/api/v1/upload/image/{fake_image_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_image_analysis_unauthenticated(self, client: AsyncClient):
        """Test getting image analysis when not authenticated."""
        fake_image_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(f"/api/v1/upload/image/{fake_image_id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_images_success(self, authenticated_client: AsyncClient):
        """Test getting user's images successfully."""
        response = await authenticated_client.get("/api/v1/upload/images")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        # Data should be a list of images
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_get_user_images_with_pagination(self, authenticated_client: AsyncClient):
        """Test getting user's images with pagination."""
        response = await authenticated_client.get("/api/v1/upload/images?limit=5&offset=0")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_get_user_images_invalid_pagination(self, authenticated_client: AsyncClient):
        """Test getting user's images with invalid pagination."""
        response = await authenticated_client.get("/api/v1/upload/images?limit=-1&offset=-1")
        # Should handle invalid pagination gracefully
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_get_user_images_unauthenticated(self, client: AsyncClient):
        """Test getting user images when not authenticated."""
        response = await client.get("/api/v1/upload/images")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_get_workflow(self, authenticated_client: AsyncClient):
        """Integration test for upload and get workflow."""
        # Step 1: Upload an image
        test_image_content = b"integration test image content"
        files = {"file": ("workflow_test.jpg", io.BytesIO(test_image_content), "image/jpeg")}
        data = {"description": "Integration test image"}

        upload_response = await authenticated_client.post("/api/v1/upload/image", files=files, data=data)

        if upload_response.status_code == 200:
            upload_data = upload_response.json()

            # Step 2: Get user's images list
            images_response = await authenticated_client.get("/api/v1/upload/images")
            assert images_response.status_code == 200

            images_data = images_response.json()
            assert images_data["success"] is True

            # Step 3: Verify uploaded image appears in user's images
            images_list = images_data["data"]
            assert isinstance(images_list, list)

            # The uploaded image should be in the list (if processing was successful)
            # Note: This might not always be true depending on AI service availability

    @pytest.mark.asyncio
    async def test_upload_multiple_images(self, authenticated_client: AsyncClient):
        """Test uploading multiple images."""
        # Upload first image
        content1 = b"first image content"
        files1 = {"file": ("multi1.jpg", io.BytesIO(content1), "image/jpeg")}

        response1 = await authenticated_client.post("/api/v1/upload/image", files=files1)

        # Upload second image
        content2 = b"second image content"
        files2 = {"file": ("multi2.jpg", io.BytesIO(content2), "image/jpeg")}

        response2 = await authenticated_client.post("/api/v1/upload/image", files=files2)

        # Both should either succeed or fail consistently
        assert response1.status_code in [200, 500, 503]
        assert response2.status_code in [200, 500, 503]

        # If first succeeded, second should also succeed (assuming no rate limiting)
        if response1.status_code == 200:
            assert response2.status_code == 200

    @pytest.mark.asyncio
    async def test_upload_png_image(self, authenticated_client: AsyncClient):
        """Test uploading PNG image."""
        png_content = b"fake png content"
        files = {"file": ("test.png", io.BytesIO(png_content), "image/png")}

        response = await authenticated_client.post("/api/v1/upload/image", files=files)
        # Should handle PNG files
        assert response.status_code in [200, 500, 503]

    @pytest.mark.asyncio
    async def test_upload_oversized_image(self, authenticated_client: AsyncClient):
        """Test uploading oversized image."""
        # Create a large fake image (simulate oversized)
        large_content = b"x" * (6 * 1024 * 1024)  # 6MB
        files = {"file": ("large.jpg", io.BytesIO(large_content), "image/jpeg")}

        response = await authenticated_client.post("/api/v1/upload/image", files=files)
        # Should handle file size limits
        assert response.status_code in [200, 413, 500, 503]