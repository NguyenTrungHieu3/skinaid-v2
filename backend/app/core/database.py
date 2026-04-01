from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from typing import AsyncGenerator

engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=True,   
    future=True,
    pool_pre_ping=True, 
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    import app.shared.models_registry  # noqa: F401
    async with engine.begin() as conn:
        try:
            await conn.run_sync(lambda conn: SQLModel.metadata.create_all(conn, checkfirst=True))
        except Exception as e:
            if "already exists" in str(e):
                pass  # tables/indexes đã tồn tại, bỏ qua
            else:
                raise