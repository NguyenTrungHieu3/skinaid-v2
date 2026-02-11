import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.core.Security.password import hash_password
from app.modules.auth.exceptions import (
    AccountInactiveError,
    AccountUnverifiedError,
    EmailExistsError,
    InvalidCredentialsError,
    InvalidCurrentPasswordError,
    InvalidResetTokenError,
    InvalidTokenError,
    TokenReuseError,
    TokenRevokedError,
    UserNotFoundError,
    UsernameExistsError,
    WeakPasswordError,
)
from app.modules.auth.models.user import User
from app.modules.auth.schemas.api import UserCreate
from app.modules.auth.service import AuthService


def make_service() -> tuple[AuthService, AsyncMock, AsyncMock, AsyncMock, Mock]:
    user_repo = AsyncMock()
    token_repo = AsyncMock()
    db = AsyncMock()
    email_service = Mock()
    email_service.generate_verification_token.return_value = "mock-token"
    email_service.send_password_reset_email_async = Mock(return_value=None)
    email_service.send_password_changed_notification_async = Mock(return_value=None)
    service = AuthService(user_repo=user_repo, token_repo=token_repo, db=db, email_service=email_service)
    return service, user_repo, token_repo, db, email_service


def valid_signup_payload() -> UserCreate:
    return UserCreate(
        user_name="new_user",
        email="new_user@example.com",
        password="StrongPass1!",
        confirm_password="StrongPass1!",
        gender="male",
    )


@pytest.mark.asyncio
async def test_register_user_success():
    service, user_repo, _, db, _ = make_service()
    payload = valid_signup_payload()
    created = User(
        user_name=payload.user_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_active=True,
        is_verified=False,
        is_deleted=False,
    )
    user_repo.email_exists.return_value = False
    user_repo.username_exists.return_value = False
    user_repo.create_with_profile.return_value = created
    service._send_verification_email = AsyncMock()

    result = await service.register_user(payload)

    assert result.email == payload.email
    user_repo.create_with_profile.assert_awaited_once()
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_register_user_fail_weak_password():
    service, *_ = make_service()
    payload = UserCreate(
        user_name="new_user",
        email="new_user@example.com",
        password="weakpass1",
        confirm_password="weakpass1",
        gender="male",
    )
    with pytest.raises(WeakPasswordError):
        await service.register_user(payload)


@pytest.mark.asyncio
async def test_register_user_fail_duplicate_email():
    service, user_repo, *_ = make_service()
    payload = valid_signup_payload()
    user_repo.email_exists.return_value = True
    with pytest.raises(EmailExistsError):
        await service.register_user(payload)


@pytest.mark.asyncio
async def test_register_user_fail_duplicate_username():
    service, user_repo, *_ = make_service()
    payload = valid_signup_payload()
    user_repo.email_exists.return_value = False
    user_repo.username_exists.return_value = True
    with pytest.raises(UsernameExistsError):
        await service.register_user(payload)


@pytest.mark.asyncio
async def test_authenticate_user_fail_not_found():
    service, user_repo, *_ = make_service()
    user_repo.get_by_username.return_value = None
    with pytest.raises(InvalidCredentialsError):
        await service.authenticate_user("missing", "Pass123!")


@pytest.mark.asyncio
async def test_authenticate_user_fail_inactive():
    service, user_repo, *_ = make_service()
    user_repo.get_by_username.return_value = User(
        user_name="inactive",
        email="inactive@example.com",
        hashed_password=hash_password("ValidPass1!"),
        is_active=False,
        is_verified=True,
        is_deleted=False,
    )
    with pytest.raises(AccountInactiveError):
        await service.authenticate_user("inactive", "ValidPass1!")


@pytest.mark.asyncio
async def test_authenticate_user_fail_unverified():
    service, user_repo, *_ = make_service()
    user_repo.get_by_username.return_value = User(
        user_name="unverified",
        email="unverified@example.com",
        hashed_password=hash_password("ValidPass1!"),
        is_active=True,
        is_verified=False,
        is_deleted=False,
    )
    with pytest.raises(AccountUnverifiedError):
        await service.authenticate_user("unverified", "ValidPass1!")


@pytest.mark.asyncio
async def test_authenticate_user_fail_wrong_password():
    service, user_repo, *_ = make_service()
    user_repo.get_by_username.return_value = User(
        user_name="verified",
        email="verified@example.com",
        hashed_password=hash_password("ValidPass1!"),
        is_active=True,
        is_verified=True,
        is_deleted=False,
    )
    with pytest.raises(InvalidCredentialsError):
        await service.authenticate_user("verified", "WrongPass1!")


@pytest.mark.asyncio
async def test_authenticate_user_success():
    service, user_repo, _, db, _ = make_service()
    user_id = uuid.uuid4()
    user_repo.get_by_username.return_value = User(
        user_id=user_id,
        user_name="verified",
        email="verified@example.com",
        hashed_password=hash_password("ValidPass1!"),
        is_active=True,
        is_verified=True,
        is_deleted=False,
    )
    updated = User(
        user_id=user_id,
        user_name="verified",
        email="verified@example.com",
        hashed_password=hash_password("ValidPass1!"),
        is_active=True,
        is_verified=True,
        is_deleted=False,
    )
    user_repo.get_by_id_with_details.return_value = updated

    result = await service.authenticate_user("verified", "ValidPass1!")

    assert result.user_id == user_id
    user_repo.update_last_activity.assert_awaited_once()
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_refresh_token_fail_invalid_payload_type():
    service, *_ = make_service()
    with patch("app.core.Security.jwt.JWTHandler.decode_token", return_value={"sub": "x", "type": "access", "jti": "j"}):
        with pytest.raises(InvalidTokenError):
            await service.refresh_token("invalid")


@pytest.mark.asyncio
async def test_refresh_token_fail_token_reuse():
    service, *_ = make_service()
    service.check_token_reuse = AsyncMock(side_effect=TokenReuseError())
    payload = {"sub": str(uuid.uuid4()), "type": "refresh", "ver": 0, "jti": "old-jti"}
    with patch("app.core.Security.jwt.JWTHandler.decode_token", return_value=payload):
        with pytest.raises(TokenReuseError):
            await service.refresh_token("refresh-token")


@pytest.mark.asyncio
async def test_refresh_token_fail_token_version_revoked():
    service, *_ = make_service()
    service.check_token_reuse = AsyncMock()
    service.validate_token_version = AsyncMock(side_effect=TokenRevokedError())
    payload = {"sub": str(uuid.uuid4()), "type": "refresh", "ver": 0, "jti": "old-jti"}
    with patch("app.core.Security.jwt.JWTHandler.decode_token", return_value=payload):
        with pytest.raises(TokenRevokedError):
            await service.refresh_token("refresh-token")


@pytest.mark.asyncio
async def test_refresh_token_success_rotation_flow():
    service, *_ = make_service()
    user_id = uuid.uuid4()
    user = User(
        user_id=user_id,
        user_name="verified",
        email="verified@example.com",
        hashed_password=hash_password("ValidPass1!"),
        is_active=True,
        is_verified=True,
        is_deleted=False,
    )
    payload = {"sub": str(user_id), "type": "refresh", "ver": 0, "jti": "old-jti"}
    new_tokens = {
        "access_token": "new-access",
        "refresh_token": "new-refresh",
        "access_jti": "new-access-jti",
        "refresh_jti": "new-refresh-jti",
        "refresh_exp": SimpleNamespace(tzinfo=None),
    }
    service.check_token_reuse = AsyncMock()
    service.validate_token_version = AsyncMock()
    service.revoke_token_family = AsyncMock(return_value=2)
    service.get_user_by_id = AsyncMock(return_value=user)
    service.get_user_token_version = AsyncMock(return_value=0)
    service.create_token_family = AsyncMock()

    with patch("app.core.Security.jwt.JWTHandler.decode_token", return_value=payload):
        with patch("app.core.Security.jwt.JWTHandler.create_token_pair", return_value=new_tokens):
            result = await service.refresh_token("refresh-token")

    assert result["access_token"] == "new-access"
    assert result["refresh_token"] == "new-refresh"
    assert result["user"].user_id == user_id


@pytest.mark.asyncio
async def test_revoke_all_user_tokens_success():
    service, user_repo, _, db, _ = make_service()
    user_id = uuid.uuid4()
    user_repo.increment_token_version.return_value = (1, 2)

    result = await service.revoke_all_user_tokens(user_id)

    assert result["old_version"] == 1
    assert result["new_version"] == 2
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_revoke_all_user_tokens_fail_user_not_found():
    service, user_repo, *_ = make_service()
    user_repo.increment_token_version.return_value = None
    with pytest.raises(UserNotFoundError):
        await service.revoke_all_user_tokens(uuid.uuid4())


@pytest.mark.asyncio
async def test_initiate_password_reset_unknown_email_returns_true():
    service, user_repo, *_ = make_service()
    user_repo.get_by_email.return_value = None
    with patch("app.modules.auth.service.random.uniform", return_value=0):
        with patch("app.modules.auth.service.asyncio.sleep", new=AsyncMock()) as sleep_mock:
            result = await service.initiate_password_reset("unknown@example.com")
    assert result is True
    sleep_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_reset_password_fail_invalid_token():
    service, _, token_repo, *_ = make_service()
    token_repo.get_valid_verification_token.return_value = None
    with pytest.raises(InvalidResetTokenError):
        await service.reset_password("user@example.com", "bad-token", "StrongPass1!")


@pytest.mark.asyncio
async def test_change_password_fail_invalid_old_password():
    service, user_repo, *_ = make_service()
    user_id = uuid.uuid4()
    user_repo.get_by_id_with_details.return_value = User(
        user_id=user_id,
        user_name="verified",
        email="verified@example.com",
        hashed_password=hash_password("ValidPass1!"),
        is_active=True,
        is_verified=True,
        is_deleted=False,
    )
    with pytest.raises(InvalidCurrentPasswordError):
        await service.change_password(user_id, "WrongPass1!", "NewStrongPass1!")


@pytest.mark.asyncio
async def test_change_password_fail_weak_new_password():
    service, user_repo, *_ = make_service()
    user_id = uuid.uuid4()
    user_repo.get_by_id_with_details.return_value = User(
        user_id=user_id,
        user_name="verified",
        email="verified@example.com",
        hashed_password=hash_password("ValidPass1!"),
        is_active=True,
        is_verified=True,
        is_deleted=False,
    )
    with pytest.raises(WeakPasswordError):
        await service.change_password(user_id, "ValidPass1!", "weak")


@pytest.mark.asyncio
async def test_change_password_success():
    service, user_repo, _, db, _ = make_service()
    user_id = uuid.uuid4()
    user = User(
        user_id=user_id,
        user_name="verified",
        email="verified@example.com",
        hashed_password=hash_password("ValidPass1!"),
        is_active=True,
        is_verified=True,
        is_deleted=False,
    )
    user_repo.get_by_id_with_details.return_value = user
    service._fire_and_forget = Mock()

    result = await service.change_password(user_id, "ValidPass1!", "NewStrongPass1!")

    assert result is True
    db.flush.assert_awaited()
    db.commit.assert_awaited()
