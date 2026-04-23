import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text, select, func
from sqlalchemy.orm import sessionmaker
from app.modules.firstaid.models.firstaid_guide import FirstAidGuide

async def main():
    try:
        engine = create_async_engine('postgresql+asyncpg://postgres:123456@localhost:5432/skinaid_db_v2')
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            stmt = select(FirstAidGuide.wound_type, FirstAidGuide.severity, FirstAidGuide.sub_type).where(
                func.lower(FirstAidGuide.wound_type) == "burn",
                func.lower(FirstAidGuide.severity) == "moderate",
                func.lower(FirstAidGuide.sub_type) == "rách da"
            )
            result = await session.execute(stmt)
            print("Query 1 (rách da):", result.fetchall())
            
            stmt2 = select(FirstAidGuide.wound_type, FirstAidGuide.severity, FirstAidGuide.sub_type).where(
                func.lower(FirstAidGuide.wound_type) == "burn",
                func.lower(FirstAidGuide.severity) == "moderate",
                func.lower(FirstAidGuide.sub_type) == "phồng rộp"
            )
            result2 = await session.execute(stmt2)
            print("Query 2 (phồng rộp):", result2.fetchall())
            
    except Exception as e:
        print(e)

if __name__ == "__main__":
    asyncio.run(main())
