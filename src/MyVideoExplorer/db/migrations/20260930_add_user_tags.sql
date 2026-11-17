-- @migration
-- db: media
-- purpose: Add user_tags column for custom user-defined tags

ALTER TABLE media_file
ADD COLUMN IF NOT EXISTS user_tags VARCHAR[] DEFAULT [];
