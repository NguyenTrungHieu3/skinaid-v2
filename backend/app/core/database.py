from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from typing import AsyncGenerator

engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=getattr(settings, "DB_ECHO", False),
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
    import logging
    logger = logging.getLogger(__name__)

    async with engine.begin() as conn:
        from sqlalchemy import inspect as sa_inspect

        def _create_tables_if_needed(connection):
            inspector = sa_inspect(connection)
            existing_tables = set(inspector.get_table_names())

            if existing_tables:
                # DB was initialized via SQL file — skip create_all
                # to avoid DuplicateTableError on indexes
                expected = set(SQLModel.metadata.tables.keys())
                missing = expected - existing_tables
                if missing:
                    logger.warning(
                        f"DB has {len(existing_tables)} tables but missing: {missing}. "
                        f"Please update your SQL schema file."
                    )
                else:
                    logger.info(
                        f"Database already initialized ({len(existing_tables)} tables). "
                        f"Skipping create_all."
                    )
                return

            # First-time setup — no tables exist, create everything
            logger.info("Empty database detected. Running create_all...")
            SQLModel.metadata.create_all(connection, checkfirst=True)
            logger.info("Database tables created successfully.")

        await conn.run_sync(_create_tables_if_needed)