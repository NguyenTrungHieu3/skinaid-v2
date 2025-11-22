import asyncio
import os
import sys

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import get_engine

async def drop_constraint():
    print("Connecting to database...")
    engine = get_engine()
    
    if not engine:
        print("Failed to get database engine")
        return

    try:
        async with engine.begin() as conn:
            print("Dropping constraint 'chk_sub_type_valid' if it exists...")
            await conn.execute(text("ALTER TABLE firstaid_guides DROP CONSTRAINT IF EXISTS chk_sub_type_valid"))
            print("Constraint dropped successfully (or didn't exist).")
            
    except Exception as e:
        print(f"Error dropping constraint: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(drop_constraint())
