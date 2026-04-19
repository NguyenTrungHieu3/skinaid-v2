import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:123456@localhost:5432/skinaid_db_v2"

WOUND_TYPE_MAP = {
    "bỏng": "burn",
    "bỏng (burn)": "burn",
    "trầy xước": "abrasion",
    "trầy xước (abrasion)": "abrasion",
    "bầm tím": "bruise",
    "bầm tím (bruise)": "bruise",
    "nấm da": "fungal",
    "nấm da (fungal)": "fungal",
    "mụn trứng cá": "acne",
    "mụn trứng cá (acne)": "acne",
    "vảy nến": "psoriasis",
    "vảy nến (psoriasis)": "psoriasis",
    "vết rách": "laceration",
    "vết rách (laceration)": "laceration",
    "phát ban": "rash",
    "phát ban (rash)": "rash",
    "vết cắt": "cut",
    "vết cắt (cut)": "cut",
    "bình thường": "normal",
    "bình thường (normal)": "normal"
}

async def main():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        for vn_wt, en_wt in WOUND_TYPE_MAP.items():
            await session.execute(
                text("UPDATE questionnaires SET wound_type = :new_wt WHERE LOWER(wound_type) = :old_wt"),
                {"new_wt": en_wt, "old_wt": vn_wt}
            )
        await session.commit()
    
    print("Database wound types updated successfully!")

if __name__ == "__main__":
    asyncio.run(main())
