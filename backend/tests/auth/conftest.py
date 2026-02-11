import os
from collections.abc import AsyncGenerator, Generator
import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.database import get_session
from app.main import app
from app.modules.auth.dependencies import get_email_service
from app.modules.auth.models.permissions import Permission  # noqa: F401
from app.modules.auth.models.role_permissions import RolePermission  # noqa: F401
from app.modules.auth.models.roles import Role
from app.modules.auth.models.token_blacklist import TokenBlacklist  # noqa: F401
from app.modules.auth.models.token_family import TokenFamily
from app.modules.auth.models.user import User
from app.modules.auth.models.user_roles import UserRole  # noqa: F401
from app.modules.auth.models.verification_token import VerificationToken  # noqa: F401
from app.modules.profile.models.user_profile import UserProfile
from app.utils.mock_email_service import mock_email_service
from tests.auth.helpers import (
    build_profile,
    build_role,
    build_user,
    build_user_role,
    create_token_pair_for_user,
)

os.environ["TESTING"] = "true"

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
    future=True,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield


@pytest_asyncio.fixture(autouse=True)
async def cleanup_auth_tables() -> AsyncGenerator[None, None]:
    truncate_sql = text(
        """
        TRUNCATE TABLE
            token_blacklist,
            token_families,
            verification_tokens,
            user_roles,
            role_permissions,
            permissions,
            roles,
            user_profiles,
            users
        RESTART IDENTITY CASCADE
        """
    )
    async with TestSessionLocal() as session:
        await session.execute(truncate_sql)
        await session.commit()
    yield
    async with TestSessionLocal() as session:
        await session.execute(truncate_sql)
        await session.commit()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_session] = override_get_db
    app.dependency_overrides[get_email_service] = lambda: mock_email_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded_roles(db_session: AsyncSession) -> dict[str, Role]:
    user_role = build_role("user")
    admin_role = build_role("admin")
    db_session.add(user_role)
    db_session.add(admin_role)
    await db_session.commit()
    await db_session.refresh(user_role)
    await db_session.refresh(admin_role)
    return {"user": user_role, "admin": admin_role}


@pytest_asyncio.fixture
async def verified_user(db_session: AsyncSession, seeded_roles: dict[str, Role]) -> User:
    user = build_user(
        user_name="verified_user",
        email="verified@example.com",
        password="ValidPass1!",
        is_verified=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(build_profile(user_id=user.user_id, full_name="Verified User"))
    db_session.add(build_user_role(user.user_id, seeded_roles["user"].role_id))
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def unverified_user(db_session: AsyncSession, seeded_roles: dict[str, Role]) -> User:
    user = build_user(
        user_name="unverified_user",
        email="unverified@example.com",
        password="ValidPass1!",
        is_verified=False,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(build_profile(user_id=user.user_id, full_name="Unverified User"))
    db_session.add(build_user_role(user.user_id, seeded_roles["user"].role_id))
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession, seeded_roles: dict[str, Role]) -> User:
    user = build_user(
        user_name="inactive_user",
        email="inactive@example.com",
        password="ValidPass1!",
        is_verified=True,
        is_active=False,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(build_profile(user_id=user.user_id, full_name="Inactive User"))
    db_session.add(build_user_role(user.user_id, seeded_roles["user"].role_id))
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers_for_verified_user(db_session: AsyncSession, verified_user: User) -> dict[str, str]:
    tokens = create_token_pair_for_user(verified_user.user_id, token_version=verified_user.token_version)
    family = TokenFamily(
        user_id=verified_user.user_id,
        refresh_token_jti=tokens["refresh_jti"],
        access_token_jti=tokens["access_jti"],
        parent_jti=None,
        is_revoked=False,
        expires_at=tokens["refresh_exp"].replace(tzinfo=None),
    )
    db_session.add(family)
    await db_session.commit()
    return {"Authorization": f"Bearer {tokens['access_token']}"}
