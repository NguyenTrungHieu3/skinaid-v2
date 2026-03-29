"""
Comprehensive migration for AI Model Management (PBI-27).

This migration ensures ai_models table has ALL required columns:
- model_type (critical)
- version_tag (critical) 
- version_number
- file_hash
- name
- description
- metrics (JSONB)
- is_active
- is_beta
- is_deleted
- traffic_percentage
- deployed_at
- deployed_by
- created_at
- updated_at
- deleted_at
- deleted_by

Run with: python migrations/migration_complete_ai_models.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from app.core.database import AsyncSessionLocal


async def check_existing_columns(db):
    """Check which columns already exist in ai_models table."""
    print("\n📊 Auditing ai_models table schema...")
    
    result = await db.execute(text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'ai_models'
        ORDER BY ordinal_position
    """))
    
    columns = result.all()
    print(f"   Found {len(columns)} columns:")
    for col in columns:
        nullable = "NULL" if col[2] == "YES" else "NOT NULL"
        default = f"DEFAULT {col[3]}" if col[3] else ""
        print(f"   - {col[0]}: {col[1]} {nullable} {default}")
    
    return [col[0] for col in columns]


async def migrate():
    """Run comprehensive migration for ai_models table."""
    
    print("=" * 70)
    print("Database Migration: Complete AI Model Management Schema (PBI-27)")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            # Phase 1: Audit existing schema
            existing_columns = await check_existing_columns(db)
            
            # Phase 2: Define all required columns with migration SQL
            migrations = [
                # Clean up old columns first
                {
                    "name": "Drop old stage column",
                    "sql": """
                        ALTER TABLE ai_models 
                        DROP COLUMN IF EXISTS stage
                    """,
                    "critical": False
                },
                {
                    "name": "Drop old model_name column",
                    "sql": """
                        ALTER TABLE ai_models 
                        DROP COLUMN IF EXISTS model_name
                    """,
                    "critical": False
                },
                {
                    "name": "Drop old version column",
                    "sql": """
                        ALTER TABLE ai_models 
                        DROP COLUMN IF EXISTS version
                    """,
                    "critical": False
                },
                {
                    "name": "Drop old file_format column",
                    "sql": """
                        ALTER TABLE ai_models 
                        DROP COLUMN IF EXISTS file_format
                    """,
                    "critical": False
                },
                {
                    "name": "Drop old checksum_sha256 column",
                    "sql": """
                        ALTER TABLE ai_models 
                        DROP COLUMN IF EXISTS checksum_sha256
                    """,
                    "critical": False
                },
                {
                    "name": "Drop old accuracy column",
                    "sql": """
                        ALTER TABLE ai_models 
                        DROP COLUMN IF EXISTS accuracy
                    """,
                    "critical": False
                },
                {
                    "name": "Drop old rollback_to_model_id column",
                    "sql": """
                        ALTER TABLE ai_models 
                        DROP COLUMN IF EXISTS rollback_to_model_id
                    """,
                    "critical": False
                },
                
                # Critical columns
                {
                    "name": "model_type",
                    "sql": """
                        ALTER TABLE ai_models 
                        ADD COLUMN IF NOT EXISTS model_type VARCHAR(50) DEFAULT 'detection'
                    """,
                    "critical": True
                },
                {
                    "name": "version_tag",
                    "sql": """
                        ALTER TABLE ai_models 
                        ADD COLUMN IF NOT EXISTS version_tag VARCHAR(50)
                    """,
                    "critical": True
                },
                {
                    "name": "version_number",
                    "sql": """
                        ALTER TABLE ai_models 
                        ADD COLUMN IF NOT EXISTS version_number INTEGER DEFAULT 1
                    """,
                    "critical": False
                },
                {
                    "name": "file_hash",
                    "sql": """
                        ALTER TABLE ai_models
                        ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64)
                    """,
                    "critical": False
                },
                {
                    "name": "file_size_bytes",
                    "sql": """
                        ALTER TABLE ai_models
                        ADD COLUMN IF NOT EXISTS file_size_bytes NUMERIC
                    """,
                    "critical": False
                },
                {
                    "name": "name",
                    "sql": """
                        ALTER TABLE ai_models
                        ADD COLUMN IF NOT EXISTS name VARCHAR(200)
                    """,
                    "critical": False
                },
                {
                    "name": "description",
                    "sql": """
                        ALTER TABLE ai_models 
                        ADD COLUMN IF NOT EXISTS description TEXT
                    """,
                    "critical": False
                },
                {
                    "name": "metrics",
                    "sql": """
                        ALTER TABLE ai_models 
                        ADD COLUMN IF NOT EXISTS metrics JSONB DEFAULT '{}'::jsonb
                    """,
                    "critical": False
                },
                {
                    "name": "is_active",
                    "sql": """
                        ALTER TABLE ai_models 
                        ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT FALSE
                    """,
                    "critical": False
                },
                {
                    "name": "is_beta",
                    "sql": """
                        ALTER TABLE ai_models 
                        ADD COLUMN IF NOT EXISTS is_beta BOOLEAN DEFAULT FALSE
                    """,
                    "critical": False
                },
                {
                    "name": "is_deleted",
                    "sql": """
                        ALTER TABLE ai_models 
                        ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE
                    """,
                    "critical": False
                },
                {
                    "name": "traffic_percentage",
                    "sql": """
                        ALTER TABLE ai_models 
                        ADD COLUMN IF NOT EXISTS traffic_percentage INTEGER DEFAULT 0
                    """,
                    "critical": False
                },
                {
                    "name": "deployed_at",
                    "sql": """
                        ALTER TABLE ai_models 
                        ADD COLUMN IF NOT EXISTS deployed_at TIMESTAMP
                    """,
                    "critical": False
                },
                {
                    "name": "deployed_by",
                    "sql": """
                        ALTER TABLE ai_models 
                        ADD COLUMN IF NOT EXISTS deployed_by UUID REFERENCES users(user_id)
                    """,
                    "critical": False
                },
                {
                    "name": "deleted_at",
                    "sql": """
                        ALTER TABLE ai_models 
                        ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP
                    """,
                    "critical": False
                },
                {
                    "name": "deleted_by",
                    "sql": """
                        ALTER TABLE ai_models 
                        ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES users(user_id)
                    """,
                    "critical": False
                },
                
                # Indexes
                {
                    "name": "ix_ai_models_model_type",
                    "sql": """
                        CREATE INDEX IF NOT EXISTS ix_ai_models_model_type 
                        ON ai_models(model_type)
                    """,
                    "critical": False
                },
                {
                    "name": "ix_ai_models_version_tag",
                    "sql": """
                        CREATE INDEX IF NOT EXISTS ix_ai_models_version_tag 
                        ON ai_models(version_tag)
                    """,
                    "critical": False
                },
                {
                    "name": "ix_ai_models_is_active",
                    "sql": """
                        CREATE INDEX IF NOT EXISTS ix_ai_models_is_active 
                        ON ai_models(is_active)
                    """,
                    "critical": False
                },
                {
                    "name": "ix_ai_models_is_deleted",
                    "sql": """
                        CREATE INDEX IF NOT EXISTS ix_ai_models_is_deleted 
                        ON ai_models(is_deleted)
                    """,
                    "critical": False
                },
                {
                    "name": "ix_ai_models_version_number",
                    "sql": """
                        CREATE INDEX IF NOT EXISTS ix_ai_models_version_number 
                        ON ai_models(version_number)
                    """,
                    "critical": False
                },
                {
                    "name": "ix_ai_models_type_active",
                    "sql": """
                        CREATE INDEX IF NOT EXISTS ix_ai_models_type_active 
                        ON ai_models(model_type, is_active)
                    """,
                    "critical": False
                },
            ]
            
            # Phase 2: Execute migrations
            print("\n🔧 Running migrations...")
            critical_missing = []
            
            for i, migration in enumerate(migrations, 1):
                col_name = migration["name"]
                is_critical = migration.get("critical", False)
                
                # Check if column already exists
                if col_name.startswith("ix_"):
                    # It's an index, just try to create
                    exists = col_name in existing_columns
                else:
                    exists = col_name in existing_columns
                
                if exists:
                    print(f"  [{i:2d}/{len(migrations)}] ✓ {col_name:30s} (already exists)")
                    continue
                
                print(f"  [{i:2d}/{len(migrations)}] Adding {col_name:30s}...", end=" ")
                
                try:
                    await db.execute(text(migration["sql"]))
                    await db.commit()
                    print("✓ Success")
                    
                    # Add to existing columns list for subsequent checks
                    if not col_name.startswith("ix_"):
                        existing_columns.append(col_name)
                    
                except Exception as e:
                    error_msg = str(e)[:100]
                    if is_critical:
                        print(f"✗ CRITICAL: {error_msg}")
                        critical_missing.append(col_name)
                    else:
                        print(f"⚠ Skipped: {error_msg}")
            
            # Phase 3: Backfill version_tag for existing data
            print("\n📝 Backfilling version_tag for existing data...")
            try:
                # Set version_tag based on version_number or default
                await db.execute(text("""
                    UPDATE ai_models 
                    SET version_tag = 'v' || COALESCE(version_number::text, '1.0.0') || '.0'
                    WHERE version_tag IS NULL OR version_tag = ''
                """))
                await db.commit()
                print("   ✓ Backfilled version_tag")
            except Exception as e:
                print(f"   ⚠ Backfill warning: {str(e)[:100]}")
            
            # Phase 4: Verify critical columns
            print("\n✅ Verifying critical columns...")
            critical_columns = ["model_type", "version_tag"]
            all_critical_present = True
            
            for col in critical_columns:
                if col in existing_columns:
                    print(f"   ✓ {col}")
                else:
                    print(f"   ✗ {col} - MISSING!")
                    all_critical_present = False
            
            if not all_critical_present:
                raise Exception(f"Critical columns missing: {[c for c in critical_columns if c not in existing_columns]}")
            
            print("\n" + "=" * 70)
            print("✅ Migration completed successfully!")
            print("=" * 70)
            
            if critical_missing:
                print(f"\n⚠ WARNING: Some critical columns failed: {critical_missing}")
                print("Please review and run migration again.")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print()
    asyncio.run(migrate())
    
    print()
    print("=" * 70)
    print("Migration finished. Restart your backend server.")
    print("=" * 70)
    print()
