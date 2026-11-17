-- @migration
-- db: media
-- purpose: Add qty_played and last_played columns for play history tracking

ALTER TABLE media_file
ADD COLUMN IF NOT EXISTS qty_played INTEGER DEFAULT 0;

ALTER TABLE media_file
ADD COLUMN IF NOT EXISTS last_played DATE;
