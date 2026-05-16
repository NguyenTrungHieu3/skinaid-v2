import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.jwt import JWTHandler
from app.modules.auth.models.token_family import TokenFamily
from app.modules.users.models.user import User
from app.modules.auth.models.verification_token import VerificationToken
from tests.auth.helpers import (
    build_password_reset_token,
    create_token_pair_for_user,
)


@pytest.mark.asyncio
async def test_auth_health_check(client: AsyncClient):
    response = await client.get("/api/v1/auth/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["service"] == "auth"
    assert data["data"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_signup_success_creates_user_profile(client: AsyncClient, seeded_roles):
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "user_name": "signup_user",
            "email": "signup_user@example.com",
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
            "gender": "male",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "signup_user@example.com"
    assert body["data"]["full_name"] == "signup_user"


@pytest.mark.asyncio
async def test_signup_duplicate_email_returns_409(client: AsyncClient, verified_user):
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "user_name": "another_user",
            "email": verified_user.email,
            "password": "StrongPass1!",
            "confirm_password": "StrongPass1!",
            "gender": "female",
        },
    )
    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "AUTH_EMAIL_EXISTS"


@pytest.mark.asyncio
async def test_signin_valid_credentials_expected_200_spec(client: AsyncClient, verified_user):
    # Spec-first: this may fail until login bugs are fixed.
    response = await client.post(
        "/api/v1/auth/signin",
        json={"user_name": verified_user.user_name, "password": "ValidPass1!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]


@pytest.mark.asyncio
async def test_signin_wrong_credentials_returns_401(client: AsyncClient, verified_user):
    response = await client.post(
        "/api/v1/auth/signin",
        json={"user_name": verified_user.user_name, "password": "WrongPass1!"},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "AUTH_INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_refresh_invalid_token_returns_401(client: AsyncClient):
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-valid-jwt"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_password_reset_request_existing_email_returns_200(client: AsyncClient, verified_user):
    response = await client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": verified_user.email},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["success"] is True


@pytest.mark.asyncio
async def test_password_reset_request_unknown_email_returns_200(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "unknown@example.com"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["success"] is True


@pytest.mark.asyncio
async def test_password_reset_confirm_valid_token_returns_200(
    client: AsyncClient,
    db_session: AsyncSession,
    verified_user: User,
):
    token_value = "valid-reset-token"
    token = build_password_reset_token(verified_user.email, token_value, expires_in_hours=1)
    db_session.add(token)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "email": verified_user.email,
            "token": token_value,
            "new_password": "NewStrongPass1!",
            "confirm_password": "NewStrongPass1!",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["success"] is True


@pytest.mark.asyncio
async def test_me_with_valid_access_token_returns_200(client: AsyncClient, auth_headers_for_verified_user):
    response = await client.get("/api/v1/auth/me", headers=auth_headers_for_verified_user)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "verified@example.com"


@pytest.mark.asyncio
async def test_logout_with_token_family_revokes_tokens(
    client: AsyncClient,
    auth_headers_for_verified_user: dict[str, str],
):
    response = await client.post("/api/v1/auth/logout", headers=auth_headers_for_verified_user)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["tokens_revoked"] > 0


@pytest.mark.asyncio
async def test_logout_all_devices_increments_token_version(
    client: AsyncClient,
    db_session: AsyncSession,
    verified_user: User,
    auth_headers_for_verified_user: dict[str, str],
):
    old_version = verified_user.token_version
    response = await client.post("/api/v1/auth/logout-all-devices", headers=auth_headers_for_verified_user)
    assert response.status_code == 200
    await db_session.refresh(verified_user)
    assert verified_user.token_version == old_version + 1


@pytest.mark.asyncio
async def test_change_password_success_revokes_all(
    client: AsyncClient,
    db_session: AsyncSession,
    verified_user: User,
    auth_headers_for_verified_user: dict[str, str],
):
    old_version = verified_user.token_version
    response = await client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "ValidPass1!", "new_password": "AnotherStrong1!"},
        headers=auth_headers_for_verified_user,
    )
    assert response.status_code == 200
    await db_session.refresh(verified_user)
    assert verified_user.token_version == old_version + 1


@pytest.mark.asyncio
async def test_change_password_wrong_old_password_returns_400(
    client: AsyncClient,
    auth_headers_for_verified_user: dict[str, str],
):
    response = await client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "WrongPass1!", "new_password": "AnotherStrong1!"},
        headers=auth_headers_for_verified_user,
    )
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "AUTH_INVALID_CURRENT_PASSWORD"
