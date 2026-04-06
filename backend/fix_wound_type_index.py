import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = (
    os.getenv("DATABASE_URL", "")
    .replace("postgresql://", "postgresql+asyncpg://")
    .replace("postgres://", "postgresql+asyncpg://")
)

async def fix():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        # Drop the old unique index created by SQLModel (index=True + unique=True)
        await conn.execute(text("DROP INDEX IF EXISTS ix_questionnaires_wound_type"))
        print("✅ Dropped ix_questionnaires_wound_type")
        result = await conn.execute(
            text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename='questionnaires'")
        )
        print("Current indexes on questionnaires:")
        for r in result:
            print(f"  - {r[0]}: {r[1][:80]}")
    await engine.dispose()

asyncio.run(fix())
