-- Fix: Add missing file_size_bytes column to ai_models table
-- Run this SQL directly in your PostgreSQL database:
--   psql -U your_user -d your_database -f migrations/fix_file_size_bytes.sql
-- Or run in a database GUI (pgAdmin, DBeaver, etc.)

-- Add file_size_bytes column
ALTER TABLE ai_models 
ADD COLUMN IF NOT EXISTS file_size_bytes NUMERIC DEFAULT NULL;

-- Add file_hash column (may also be missing)
ALTER TABLE ai_models
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64) DEFAULT NULL;

-- Add description column (may also be missing)
ALTER TABLE ai_models 
ADD COLUMN IF NOT EXISTS description TEXT DEFAULT NULL;

-- Verify columns were added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'ai_models'
  AND column_name IN ('file_size_bytes', 'file_hash', 'description')
ORDER BY column_name;
