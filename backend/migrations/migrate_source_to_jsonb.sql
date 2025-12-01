-- Migration: Convert source from VARCHAR(500) to JSONB
-- Date: 2025-11-27
-- Purpose: Support structured source data with name and URL

-- BACKUP FIRST!
-- pg_dump -U your_user -d skinaid_db > backup_before_source_migration.sql

BEGIN;

-- Step 1: Add temporary JSONB column
ALTER TABLE firstaid_guides 
ADD COLUMN source_new JSONB;

-- Step 2: Migrate existing VARCHAR data to JSONB
-- Convert existing string sources to JSON object with 'name' field
UPDATE firstaid_guides
SET source_new = jsonb_build_object('name', source)
WHERE source IS NOT NULL AND source != '';

-- Step 3: Drop old VARCHAR column  
ALTER TABLE firstaid_guides 
DROP COLUMN source;

-- Step 4: Rename new column to 'source'
ALTER TABLE firstaid_guides 
RENAME COLUMN source_new TO source;

-- Step 5: Add comment
COMMENT ON COLUMN firstaid_guides.source IS 'Reference source as JSON: {name: str, url?: str}';

COMMIT;

-- Verify migration
SELECT 
    firstaidguide_id,
    title,
    source,
    jsonb_typeof(source) as source_type
FROM firstaid_guides
LIMIT 5;
