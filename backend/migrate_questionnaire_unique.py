"""
Migration: Remove unique constraint on wound_type, add partial unique index (only 1 active per wound_type)
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

print(f"Connecting to: {DATABASE_URL[:50]}...")

async def run_migration():
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        # 1. Tìm và xóa unique constraint hiện có trên wound_type
        result = await conn.execute(text("""
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'questionnaires'::regclass
              AND contype = 'u'
              AND array_to_string(ARRAY(
                SELECT attname FROM pg_attribute
                WHERE attrelid = conrelid AND attnum = ANY(conkey)
              ), ',') = 'wound_type';
        """))
        constraint = result.fetchone()
        if constraint:
            print(f"Dropping unique constraint: {constraint[0]}")
            await conn.execute(text(
                f'ALTER TABLE questionnaires DROP CONSTRAINT IF EXISTS "{constraint[0]}"'
            ))
        else:
            # Thử tên constraint phổ biến
            await conn.execute(text(
                'ALTER TABLE questionnaires DROP CONSTRAINT IF EXISTS questionnaires_wound_type_key'
            ))
            print("Dropped constraint questionnaires_wound_type_key (if existed)")

        # 2. Xóa partial unique index cũ nếu tồn tại (idempotent)
        await conn.execute(text(
            'DROP INDEX IF EXISTS uq_one_active_per_wound_type'
        ))
        print("Dropped old partial index (if existed)")

        # 3. Tạo PARTIAL UNIQUE INDEX: chỉ 1 bộ is_active=True cho mỗi wound_type
        await conn.execute(text("""
            CREATE UNIQUE INDEX uq_one_active_per_wound_type
            ON questionnaires (wound_type)
            WHERE is_active = TRUE;
        """))
        print("✅ Created partial unique index: only 1 active questionnaire per wound_type")

    await engine.dispose()
    print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_migration())
