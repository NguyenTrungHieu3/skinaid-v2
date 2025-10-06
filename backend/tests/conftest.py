import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import get_db, get_engine
from app.main import app
from app.core.config import settings

# Test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database engine."""
    engine = get_engine()
    if not engine:
        raise RuntimeError("Database not configured")

    # Create test database tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Drop test database tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest.fixture
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with AsyncSession(test_db_engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create FastAPI test client."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

@pytest.fixture
async def authenticated_client(client) -> AsyncGenerator[AsyncClient, None]:
    """Create authenticated test client."""
    # Create test user data
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "display_name": "Test User"
    }

    # Register user
    response = await client.post("/api/v1/auth/signup", json=user_data)
    assert response.status_code == 201

    # Login to get token
    login_response = await client.post("/api/v1/auth/signin", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    assert login_response.status_code == 200

    token = login_response.json()["data"]["access_token"]

    # Set authorization header
    client.headers.update({"Authorization": f"Bearer {token}"})

    yield client

@pytest.fixture
def test_image_path():
    """Path to test image file."""
    return os.path.join(os.path.dirname(__file__), "test_image.jpg")

@pytest.fixture
def sample_wound_types():
    """Sample wound types for testing."""
    return [
        {"type": "burn", "severities": ["mild", "moderate", "severe"]},
        {"type": "cut", "severities": ["mild", "moderate", "severe"]},
        {"type": "abrasion", "severities": ["mild", "moderate"]}
    ]

@pytest.fixture
def sample_first_aid_guides():
    """Sample first aid guides for testing."""
    return [
        {
            "wound_type": "burn",
            "severity": "mild",
            "instructions": "Cool the burn under cold running water for at least 10 minutes.",
            "warnings": "Do not use ice directly on the burn."
        },
        {
            "wound_type": "burn",
            "severity": "moderate",
            "instructions": "Seek medical attention. Cover the burn with a sterile bandage.",
            "warnings": "Do not break blisters."
        }
    ]