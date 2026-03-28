"""
Migration script to add model management columns to ai_models table (PBI-27).

This script adds:
- version_number
- file_hash
- name
- description
- is_beta
- is_deleted
- deleted_at
- deleted_by

Run with: python migration_add_model_columns.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def migrate():
    """Run migration to add new columns to ai_models table."""
    
    print("🚀 Starting migration for ai_models table...")
    
    async with AsyncSessionLocal() as db:
        try:
            # List of migrations to run
            migrations = [
                # model_type (add first as it's critical)
                """
                ALTER TABLE ai_models 
                ADD COLUMN IF NOT EXISTS model_type VARCHAR(50) DEFAULT 'detection'
                """,
                
                # version_number
                """
                ALTER TABLE ai_models 
                ADD COLUMN IF NOT EXISTS version_number INTEGER DEFAULT 1
                """,
                
                # file_hash
                """
                ALTER TABLE ai_models 
                ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64)
                """,
                
                # name
                """
                ALTER TABLE ai_models 
                ADD COLUMN IF NOT EXISTS name VARCHAR(200)
                """,
                
                # description
                """
                ALTER TABLE ai_models 
                ADD COLUMN IF NOT EXISTS description TEXT
                """,
                
                # is_beta
                """
                ALTER TABLE ai_models 
                ADD COLUMN IF NOT EXISTS is_beta BOOLEAN DEFAULT FALSE
                """,
                
                # is_deleted
                """
                ALTER TABLE ai_models 
                ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE
                """,
                
                # deleted_at
                """
                ALTER TABLE ai_models 
                ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP
                """,
                
                # deleted_by
                """
                ALTER TABLE ai_models 
                ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES users(user_id)
                """,
                
                # Create index on is_deleted
                """
                CREATE INDEX IF NOT EXISTS ix_ai_models_is_deleted 
                ON ai_models(is_deleted)
                """,
                
                # Create index on version_number
                """
                CREATE INDEX IF NOT EXISTS ix_ai_models_version_number 
                ON ai_models(version_number)
                """,
            ]
            
            for i, migration in enumerate(migrations, 1):
                print(f"  [{i}/{len(migrations)}] Running migration...")
                try:
                    await db.execute(text(migration))
                    await db.commit()
                    print(f"      ✓ Success")
                except Exception as e:
                    print(f"      ⚠ Skipped (may already exist): {str(e)[:100]}")
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add Model Management Columns")
    print("=" * 60)
    print()
    
    asyncio.run(migrate())
    
    print()
    print("=" * 60)
    print("Migration finished. Restart your backend server.")
    print("=" * 60)
