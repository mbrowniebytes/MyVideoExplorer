-- @migration
-- db: tag_catalog
-- purpose: Initial tag_catalog schema: schema_migrations and tags tables

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tags (
    tag TEXT PRIMARY KEY,
    color TEXT NOT NULL DEFAULT '#808080'
);

