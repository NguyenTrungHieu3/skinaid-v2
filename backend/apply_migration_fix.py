import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def run_migration():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return
        
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN last_active_at TIMESTAMP NULL;"))
            print("Successfully added last_active_at column to users table.")
        except Exception as e:
            print(f"Error executing migration: {e}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migration())
