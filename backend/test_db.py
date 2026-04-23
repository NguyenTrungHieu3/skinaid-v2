import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

async def main():
    try:
        engine = create_async_engine('postgresql+asyncpg://postgres:123456@localhost:5432/skinaid_db_v2')
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            result = await session.execute(text("SELECT wound_type, severity, sub_type, is_active FROM firstaid_guides;"))
            rows = result.fetchall()
            for row in rows:
                print(row)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    asyncio.run(main())
