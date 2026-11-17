-- @migration
-- db: media
-- purpose: Add file_size column to media_file table
ALTER TABLE media_file ADD COLUMN IF NOT EXISTS file_size BIGINT;
