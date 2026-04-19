import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def fix_db():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT conname, pg_get_constraintdef(c.oid)
            FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE conrelid = 'firstaid_guides'::regclass;
        """))
        for row in result.fetchall():
            print(row[0], row[1])

if __name__ == "__main__":
    asyncio.run(fix_db())
