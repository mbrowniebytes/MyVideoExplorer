-- @migration
-- db: filter_catalog
-- purpose: Initial filter_catalog schema: schema_migrations and media_filters tables

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS media_filters (
    filter_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    criteria JSON NOT NULL,
    folder_counts MAP(VARCHAR, BIGINT) NOT NULL,
    total_count BIGINT,
    sort_order INTEGER NOT NULL
);

