-- Initial schema for tag_catalog.db

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tags (
    tag TEXT PRIMARY KEY,
    color TEXT NOT NULL DEFAULT '#808080'
);

