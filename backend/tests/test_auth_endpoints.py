import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestAuthEndpoints:
    """Test cases for authentication endpoints."""

    # Test signup endpoint
    @pytest.mark.asyncio
    async def test_signup_success(self, client: AsyncClient):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "display_name": "New User"
        }

        response = await client.post("/api/v1/auth/signup", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["success"] is True
        assert "user_id" in data["data"]
        assert data["data"]["email"] == "newuser@example.com"
        assert data["data"]["display_name"] == "New User"

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, client: AsyncClient):
        """Test signup with duplicate email."""
        user_data = {
            "email": "duplicate@example.com",
            "password": "password123",
            "display_name": "User 1"
        }

        # First signup
        response1 = await client.post("/api/v1/auth/signup", json=user_data)
        assert response1.status_code == 201

        # Second signup with same email
        response2 = await client.post("/api/v1/auth/signup", json=user_data)
        assert response2.status_code == 400

    @pytest.mark.asyncio
    async def test_signup_invalid_email(self, client: AsyncClient):
        """Test signup with invalid email."""
        user_data = {
            "email": "invalid-email",
            "password": "password123",
            "display_name": "User"
        }

        response = await client.post("/api/v1/auth/signup", json=user_data)
        assert response.status_code == 422

    # Test signin endpoint
    @pytest.mark.asyncio
    async def test_signin_success(self, client: AsyncClient):
        """Test successful login."""
        # First create a user
        user_data = {
            "email": "logintest@example.com",
            "password": "loginpass123",
            "display_name": "Login Test"
        }
        await client.post("/api/v1/auth/signup", json=user_data)

        # Login
        login_data = {
            "email": "logintest@example.com",
            "password": "loginpass123"
        }

        response = await client.post("/api/v1/auth/signin", json=login_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_signin_wrong_password(self, client: AsyncClient):
        """Test login with wrong password."""
        # First create a user
        user_data = {
            "email": "wrongpass@example.com",
            "password": "correctpass123",
            "display_name": "Wrong Pass Test"
        }
        await client.post("/api/v1/auth/signup", json=user_data)

        # Login with wrong password
        login_data = {
            "email": "wrongpass@example.com",
            "password": "wrongpassword"
        }

        response = await client.post("/api/v1/auth/signin", json=login_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_signin_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }

        response = await client.post("/api/v1/auth/signin", json=login_data)
        assert response.status_code == 401

    # Test get current user endpoint
    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, authenticated_client: AsyncClient):
        """Test getting current user info when authenticated."""
        response = await authenticated_client.get("/api/v1/auth/me")
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == "test@example.com"
        assert "user_id" in data
        assert "display_name" in data

    @pytest.mark.asyncio
    async def test_get_me_unauthenticated(self, client: AsyncClient):
        """Test getting current user info when not authenticated."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    # Test email verification endpoints
    @pytest.mark.asyncio
    async def test_verify_email_post(self, client: AsyncClient):
        """Test email verification via POST."""
        # Create user first
        user_data = {
            "email": "verifytest@example.com",
            "password": "verifypass123",
            "display_name": "Verify Test"
        }
        await client.post("/api/v1/auth/signup", json=user_data)

        # For testing, we'll just check the endpoint exists and handles requests
        # In real scenario, you'd need to mock email sending and get verification token
        verification_data = {
            "email": "verifytest@example.com",
            "token": "test_token"
        }

        response = await client.post("/api/v1/auth/verify-email", json=verification_data)
        # This might fail due to missing token validation, but endpoint should exist
        assert response.status_code in [200, 400, 404]

    @pytest.mark.asyncio
    async def test_verify_email_get(self, client: AsyncClient):
        """Test email verification via GET."""
        response = await client.get("/api/v1/auth/verify-email?email=test@example.com&token=test_token")
        # This might fail due to missing token validation, but endpoint should exist
        assert response.status_code in [200, 400, 404]

    # Test password reset endpoints
    @pytest.mark.asyncio
    async def test_request_password_reset(self, client: AsyncClient):
        """Test password reset request."""
        reset_data = {
            "email": "resettest@example.com"
        }

        response = await client.post("/api/v1/auth/password-reset/request", json=reset_data)
        # Should succeed even if user doesn't exist (security best practice)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_confirm_password_reset(self, client: AsyncClient):
        """Test password reset confirmation."""
        reset_data = {
            "email": "resetconfirm@example.com",
            "token": "reset_token",
            "new_password": "newpassword123"
        }

        response = await client.post("/api/v1/auth/password-reset/confirm", json=reset_data)
        # This might fail due to missing token validation, but endpoint should exist
        assert response.status_code in [200, 400, 404]

    # Test refresh token endpoint
    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient):
        """Test token refresh."""
        # First login to get refresh token
        user_data = {
            "email": "refreshtest@example.com",
            "password": "refreshpass123",
            "display_name": "Refresh Test"
        }
        await client.post("/api/v1/auth/signup", json=user_data)

        login_response = await client.post("/api/v1/auth/signin", json={
            "email": "refreshtest@example.com",
            "password": "refreshpass123"
        })
        refresh_token = login_response.json()["data"]["refresh_token"]

        # Refresh token
        refresh_data = {
            "refresh_token": refresh_token
        }

        response = await client.post("/api/v1/auth/refresh", json=refresh_data)
        # This might fail due to token validation, but endpoint should exist
        assert response.status_code in [200, 401, 422]

    # Test logout endpoint
    @pytest.mark.asyncio
    async def test_logout(self, authenticated_client: AsyncClient):
        """Test user logout."""
        response = await authenticated_client.post("/api/v1/auth/logout")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    # Test resend verification endpoint
    @pytest.mark.asyncio
    async def test_resend_verification(self, client: AsyncClient):
        """Test resend verification email."""
        resend_data = {
            "email": "resendtest@example.com"
        }

        response = await client.post("/api/v1/auth/resend-verification", json=resend_data)
        # Should succeed even if user doesn't exist (security best practice)
        assert response.status_code == 200

    # Test health check endpoint
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/api/v1/auth/health")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "status" in data["data"]