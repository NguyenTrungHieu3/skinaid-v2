"""
Migration to drop old columns from ai_models table.

Run this FIRST before running migration_complete_ai_models.py

Run with: python migrations/migration_drop_old_columns.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def migrate():
    """Drop old columns from ai_models table."""
    
    print("=" * 70)
    print("Database Migration: Drop Old Columns from ai_models")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            # List of old columns to drop
            old_columns = [
                "stage",
                "model_name", 
                "version",
                "file_format",
                "checksum_sha256",
                "accuracy",
                "rollback_to_model_id",
                "file_size_mb"
            ]
            
            print("\n🗑️  Dropping old columns...")
            
            for col in old_columns:
                print(f"  Dropping {col:30s}...", end=" ")
                try:
                    # Use CASCADE to drop dependent objects
                    await db.execute(text(f"""
                        ALTER TABLE ai_models 
                        DROP COLUMN IF EXISTS {col} CASCADE
                    """))
                    await db.commit()
                    print("✓ Success")
                except Exception as e:
                    print(f"⚠ Skipped: {str(e)[:80]}")
            
            print("\n" + "=" * 70)
            print("✅ Migration completed successfully!")
            print("=" * 70)
            print("\n⚠️  IMPORTANT: Now run migration_complete_ai_models.py")
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print()
    asyncio.run(migrate())
    
    print()
    print("=" * 70)
    print("Migration finished. Run migration_complete_ai_models.py next.")
    print("=" * 70)
    print()
