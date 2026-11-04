-- Add filter_groups table and extend media_filters with group_id, is_system, is_visible, last_modified

CREATE TABLE IF NOT EXISTS filter_groups (
    group_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE
);

ALTER TABLE media_filters
    ADD COLUMN IF NOT EXISTS group_id BIGINT;

ALTER TABLE media_filters
    ADD COLUMN IF NOT EXISTS is_system BOOLEAN DEFAULT FALSE;

ALTER TABLE media_filters
    ADD COLUMN IF NOT EXISTS is_visible BOOLEAN DEFAULT TRUE;

ALTER TABLE media_filters
    ADD COLUMN IF NOT EXISTS last_modified TIMESTAMPTZ;

-- Set defaults for existing rows
UPDATE media_filters SET is_system = FALSE WHERE is_system IS NULL;
UPDATE media_filters SET is_visible = TRUE WHERE is_visible IS NULL;
UPDATE media_filters SET last_modified = CURRENT_TIMESTAMP WHERE last_modified IS NULL;

-- Seed system groups (use fixed snowflake-like IDs)
INSERT INTO filter_groups (group_id, name, is_system) VALUES
    (1002, 'Favorites', TRUE),
    (1003, 'Watchlist', TRUE),
    (1004, 'Edited Recently', TRUE)
ON CONFLICT (name) DO NOTHING;

