import os
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

async_engine: Optional[AsyncEngine] = None
async_session_maker = None

def get_engine():
    global async_engine
    if async_engine is None and settings.DATABASE_URL:
        if settings.DATABASE_URL.startswith("sqlite"):
            async_engine = create_async_engine(
                url=settings.DATABASE_URL, 
                echo=True, 
                future=True,
            )
        else:
            async_engine = create_async_engine(
                url=settings.DATABASE_URL, 
                echo=True, 
                future=True,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo_pool=True,
            )
    return async_engine

def get_session_maker():
    global async_session_maker
    if async_session_maker is None:
        engine = get_engine()
        if engine:
            async_session_maker = async_sessionmaker(
                bind=engine, 
                autoflush=False, 
                autocommit=False, 
                expire_on_commit=False, 
                class_=AsyncSession
            )
    return async_session_maker

@asynccontextmanager
async def get_db(): 
    session_maker = get_session_maker()
    if not session_maker:
        raise RuntimeError("Database not configured")
    session: AsyncSession = session_maker()
    try: 
        yield session
        await session.commit()
    except: 
        await session.rollback()
        raise
    finally: 
        await session.close() 

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session_maker = get_session_maker()
    if not session_maker:
        raise RuntimeError("Database not configured")
    async with session_maker() as session: 
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close() 

async def init_db(): 
    from app.modules.auth.models.user import User
    from app.modules.profile.models.user_profile import UserProfile
    from app.modules.auth.models.verification_token import VerificationToken
    from app.modules.upload.models.wound_images import WoundImages
    from app.modules.upload.models.upload_validations import UploadValidation
    from app.modules.firstaid.models.firstaid_guide import FirstAidGuide
    
    engine = get_engine()
    if not engine:
        raise RuntimeError("Database not configured")
    
    async with engine.begin() as conn: 
        await conn.run_sync(SQLModel.metadata.create_all)